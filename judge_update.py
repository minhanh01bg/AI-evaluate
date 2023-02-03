import os
import cv2
import numpy as np
import pandas as pd
import psutil

class BoundBox:
    def __init__(self, ymin, xmin , ymax , xmax, objness=None, classes=None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.objness = objness
        self.classes = classes
        self.label = -1
        self.score = -1

    def get_label(self):
        if self.label == -1:
            self.label = np.argmax(self.classes)

        return self.label

    def get_score(self):
        if self.score == -1:
            self.score = self.classes[self.get_label()]

        return self.score
    
    
# x1,y1 ----------
#       |        |
#       |        |
#       |        |
#       ----------x2,y2
def _interval_overlap(interval_a, interval_b):
    x1, x2 = interval_a
    x3, x4 = interval_b
    if x3 < x1:
        if x4 < x1:
            return 0
        else:
            return min(x2, x4) - x1
    else:
        if x2 < x3:
            return 0
        else:
            return min(x2, x4) - x3

# IoU = (A intersection B) / (A union B)
def bbox_iou(box1, box2):
    intersect_w = _interval_overlap(
        [box1.xmin, box1.xmax], [box2.xmin, box2.xmax])
    intersect_h = _interval_overlap(
        [box1.ymin, box1.ymax], [box2.ymin, box2.ymax])
    intersect = intersect_w * intersect_h
    w1, h1 = box1.xmax-box1.xmin, box1.ymax-box1.ymin
    w2, h2 = box2.xmax-box2.xmin, box2.ymax-box2.ymin
    union = w1*h1 + w2*h2 - intersect
    if union == 0: 
        return 0
    return float(intersect) / union


def create_box(a):
    return BoundBox(a[0],a[1],a[2],a[3]) # y1, x1, y2, x2 

# row different together
def matrix_confusion(matrix):
    convert =[]
    amount_row = len(matrix)
    amount_col = len(matrix[0])
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            convert.append([i,j,matrix[i][j]])
    df = pd.DataFrame(convert, columns=['row','col','score'])
    # print(df)
    # convert row, col, score to matrix
    convert = df.values
    convert = convert.tolist()
    convert = sorted(convert, key=lambda x: x[2], reverse=True)
    # print(convert)
    
    dict_col = []
    dict_row = []
    values = []
    for i in range(len(convert)):
        if str(convert[i][0]) not in dict_row and str(convert[i][1]) not in dict_col:
            dict_col.append(str(convert[i][1]))
            dict_row.append(str(convert[i][0]))
            values.append(float(convert[i][2]))
    
    values = pd.DataFrame({'row':dict_row, 'col':dict_col, 'score':values})
    # if IoU ≥0.5, classify the object detection as True Positive(TP)
    acc_values = values.loc[values['score'] >= 0.5]
    TP = len(acc_values)
    # if Iou <0.5, then it is a wrong detection and classify it as False Positive(FP)
    FP = len(values) - len(acc_values)
    if amount_col > amount_row:
        FP = FP + (amount_col - amount_row)
    # When a ground truth is present in the image and model failed to detect the object, classify it as False Negative(FN).
    FN = amount_row - amount_col
    # True Negative (TN): TN is every part of the image where we did not predict an object. This metrics is not useful for object detection, hence we ignore TN.
    return TP, FP, FN

def precision_recall(TP, FP, FN):
    # precision = TP / (TP + FP)
    # recall = TP / (TP + FN)
    if TP + FN == 0 and TP + FP ==0:
        return 0,0
    if TP + FP == 0:
        return 0,TP / (TP + FN)
    
    if TP + FN == 0:
        return TP / (TP + FP), 0
    return TP / (TP + FP), TP / (TP + FN)

def f1_score(precision, recall):
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)

def accuracy(TP, FP, FN):
    if TP + FP + FN == 0:
        return 0
    return TP / (TP + FP + FN)


TP_,FN_,FP_ = [],[],[]
def scrore_frame_x(dict_trust,dict_predict):
    if len(dict_trust) == 0:
        return 1.0,1.0,1.0,1.0,0,0,0
    TP = 0
    FP = 0
    FN = 0
    TN = 0
    acc_ls = []
    f1_score_ls = []
    precision_ls = []
    recall_ls = []
    
    for key in dict_trust:
        if key in dict_predict:
            matrix_score = []
            
            for i in range(len(dict_trust[key])):
                ls = []
                for j in range(len(dict_predict[key])):
                    ls.append(bbox_iou(create_box(dict_trust[key][i]),create_box(dict_predict[key][j])))
                    
                matrix_score.append(ls)
                
            # matrix_score = np.array(matrix_score)
            # matrix_score = pd.DataFrame(matrix_score)
            # matrix_score.to_csv('./matrix_score2.csv')
            TP, FP, FN = matrix_confusion(matrix_score)
            acc_ls.append(accuracy(TP, FP, FN))
            precision_ls.append(precision_recall(TP, FP, FN)[0])
            recall_ls.append(precision_recall(TP, FP, FN)[1])
            f1_score_ls.append(f1_score(precision_recall(TP, FP, FN)[0],precision_recall(TP, FP, FN)[1]))
            TP_.append(TP)
            FN_.append(FN)
            FP_.append(FP)
    return np.mean(acc_ls), np.mean(precision_ls), np.mean(recall_ls), np.mean(f1_score_ls)
    

def process_evaluation(file_trust,file_predict):
    df_trust = pd.read_csv(file_trust)
    df_predict = pd.read_csv(file_predict)
    scores = []
    for frame in range(len(df_trust['frame_x'])):
    # print(df_trust['bounding_box'][0])
    # print(df_predict['bounding_box'][0])        
        import ast
        dict_trust = ast.literal_eval(df_trust['bounding_box'][frame])
        dict_predict = ast.literal_eval(df_predict['bounding_box'][frame])
        scores.append(scrore_frame_x(dict_trust,dict_predict))
        print(scrore_frame_x(dict_trust,dict_predict))
    
    
    process = psutil.Process(os.getpid())
    return np.mean(scores[0]), np.mean(scores[1]), np.mean(scores[2]), np.mean(scores[3]),process.memory_info().rss


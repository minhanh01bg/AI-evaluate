import csv
import numpy as np
import pandas as pd
import os
import psutil
# count_person
def evaluate_count_person(actual_path,predict_path):
    # print(actual)
    header = ['frame_x','evaluate_%']
    with open('evaluate_count_person.csv','w') as f:
        csvFile=csv.writer(f)
        csvFile.writerow(header)
        try:
            actual = pd.read_csv(actual_path)
            predict = pd.read_csv(predict_path)
            for i in range(len(actual)):
                if actual['predict'][i] == predict['predict'][i]:
                    csvFile.writerow([actual['fram_x'][i],100])
                else:
                    percent = (actual['predict'][i] - predict['predict'][i])/actual['predict'][i]
                    percent = 1 - percent
                    percent = percent * 100
                    csvFile.writerow([actual['fram_x'][i],percent])
            return True
        except KeyError as err:
            return 'KeyError', err
        except Exception as err:
            return 'Error', err
        except FileNotFoundError as err:
            return 'FileNotFoundError', err
        except:
            return 'Error'

def evaluate_end_point(evaluate_path):
    evaluate_ = pd.read_csv(evaluate_path)
    sum_ = 0
    for i in range(len(evaluate_)):
        sum_ = sum_ + evaluate_['evaluate_%'][i]
    sum_ = sum_/len(evaluate_)
    process = psutil.Process(os.getpid())
    return sum_,process.memory_info().rss # in bytes 

# bb_iou
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
    return float(intersect) / union


def create_box(a):
    return BoundBox(a[0],a[1],a[2],a[3])


def select_number(list_score):
    cnt = [i for i in list_score if i > 0.5]
    return len(cnt)

# matrix score
# return list max in matrix
def get_max_in_list(matrix_score):
    list_select = []
    for i in range(len(matrix_score)):
        max = 0
        for j in range(len(matrix_score[i])):
            if matrix_score[i][j] > max:
                max = matrix_score[i][j]
        list_select.append(max)
    list_select.sort()    
    if len(matrix_score) == len(matrix_score[0]):
        return list_select,0
    else:
        result = []
        for i in range(len(matrix_score[0])):
            result.append(list_select[i])
        return result, len(matrix_score) - len(matrix_score[0])
    

def IoU_bounding_boxs(dict_bb_actual,dict_bb_predict):
    # create file csv
    # header = ['frame_x','evaluate_%']
    # with open('evaluate_bounding_box.csv','w') as f:
    #     csvFile=csv.writer(f)
    #     csvFile.writerow(header)
    # compare bb of object
    list_percent = []
    for key in dict_bb_actual:
        # print(key,dict_bb_actual[key])
        percent_of_ob = 0
        if key in dict_bb_predict:
            # print('key in predict')
            # print(dict_bb_predict[key])
            matrix_score = []
            for i in range(len(dict_bb_actual[key])):
                ls = []
                for j in range(len(dict_bb_predict[key])):
                    box1 = create_box(dict_bb_actual[key][i])
                    box2 = create_box(dict_bb_predict[key][j])
                    ls.append(bbox_iou(box1,box2))
                matrix_score.append(ls)                
            # matrix score
            matrix_score = np.array(matrix_score)

            # select k score max in matrix and count the number of undetected objects
            list_select,cnt_not_detect = get_max_in_list(matrix_score)
            # count iou > 0.5
            # số lượng bb được chấp nhận
            cnt = select_number(list_select)
            # percent of object detection
            # phần trăm chấp nhận được của object 
            percent_of_ob = cnt/len(dict_bb_actual[key])
            list_percent.append(percent_of_ob)
        
        # object not detected
        elif key not in dict_bb_predict:
            list_percent.append(0)
        
    list_percent = np.array(list_percent)
    # return average percent
    return sum(list_percent)/len(list_percent)
    
    
def evaluate_detect_object(actual_path,predict_path):
    actual = pd.read_csv(actual_path)
    predict = pd.read_csv(predict_path)
    # print(actual)
    try:
        result = 0
        list_ = []
        for i in range(len(actual)):
            # convert string to dictionary with ast library
            import ast
            actual_ = ast.literal_eval(actual['predict'][i])
            predict_ = ast.literal_eval(predict['predict'][i])
            
            # frame not object
            if len(actual_) == 0:
                continue
            else:
                # phần trăm chấp nhận trong 1 frame
                percent_ac_fame = IoU_bounding_boxs(actual_,predict_)
                list_.append(percent_ac_fame)
        # kết quả chia trung bình
        result = sum(list_)/len(list_)
        process = psutil.Process(os.getpid())
        return result * 100,process.memory_info().rss # in bytes 
    except KeyError as err:
        return 'KeyError', err
    except:
        return 'Error'


# evaluate_license_plate_reg
# evaluate license plate recognition

def compare_string(str1,str2):
    p_ac = 0
    for x,y in zip(str1,str2):
        if x == y:
            p_ac += 1
    p_ac = p_ac/len(str1)
    return p_ac

    
def evaluate_license_plate_reg(trust_path,predict_path):
    trust_ = pd.read_csv(trust_path)
    predict_ = pd.read_csv(predict_path)
    list_percent_ac = []
    try:
        for i in range(len(trust_)):
            lp_trust_1_frame = str(trust_['predict'][i])
            lp_predict_1_frame = str(predict_['predict'][i])
            p_ac = compare_string(lp_trust_1_frame,lp_predict_1_frame)
            list_percent_ac.append(p_ac)
        process = psutil.Process(os.getpid())
        return sum(list_percent_ac)/len(list_percent_ac)*100, process.memory_info().rss # in bytes 
    except KeyError as err:
        return 'KeyError', err
    except:
        return 'Error'


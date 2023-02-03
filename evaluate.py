import numpy as np
import pandas as pd
import csv
from flask import Flask,jsonify,request
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import datetime
from judge import evaluate_end_point,evaluate_detect_object,evaluate_license_plate_reg
import requests
import time

import shutil
from judge_update import process_evaluation
from flask import send_file
import jwt
from functools import wraps

ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ABC'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def to_seconds(hours, minutes, seconds):
    return hours * 3600 + minutes * 60 + seconds

def created_folder(path):
    try:
        os.mkdir(path)
        return True
    except:
        return False

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
        encoded = jwt.encode({"accepted": "oke"}, app.config['SECRET_KEY'], algorithm="HS256")
        print(encoded)
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # return "accepted": "oke"
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        return  f(*args, **kwargs)
    return decorated

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        id_ = request.form.get('id')
        UPLOAD_FOLDER = './trust_csv/' + id_ 
        created_folder(UPLOAD_FOLDER)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('file')
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('upload_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file multiple>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/export_report',methods=['POST'])
def export_report():
    id = str(request.form.get('id'))
    created_folder('/'+id)
    from docxtpl import DocxTemplate


@app.route('/download_images',methods=['POST'])
@token_required
def download_images():
    server = str(request.form.get('server')) +'_'
    id_ = str(request.form.get('id'))
    created_folder('./static/images_predicted')
    
    if id_ == '4623bec3-37ac-4613-9a2c-15c3fec5789c' or id_ == '41c24adf-2da4-4763-93f0-980d28d629f8':
        created_folder('./static/images_predicted/'+id_)
        for file in os.listdir('./trust_csv/'+id_):
            df = pd.read_csv('./trust_csv/'+id_+'/'+file)
            video = file.split('.')[0]
            for i in range(len(df['frame_x'])):
                url = 'http://kube-connect.zcode.vn/result_file/' + server + str(video)+'-'+str(df['frame_x'][i]) +'.jpg'
                header = {
                "Authorization": "token 6b31ae0a90ca4ea9a6b8911cf0d9ad7d",
                "Content-Type": "application/json",
                "Accept":"application/json, text/plain, */*"
                }
                r = requests.get(url, headers=header,stream=True)
                created_folder('./static/images_predicted/'+id_+'/'+video)
                if r.status_code == 200:
                    with open('./static/images_predicted/'+id_+'/'+video+'/'+df['frame_x'][i] +'.jpg','wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    print('Image sucessfully Downloaded: ','./static/images_predicted/'+id_+'/'+video+'/'+df['frame_x'][i] +'.jpg')
                else:
                    print('Image Couldn\'t be retrieved')
                        
    return jsonify({'message':'download images sucessfully'})
    

@app.route('/evaluate',methods=['POST'])
def evaluate():
    time_current = datetime.datetime.now()
    try:
        id_ = str(request.form.get('id'))
        server = str(request.form.get('server')) + "_"
        
        # count person and count car
        if id_ == '4623bec3-37ac-4613-9a2c-15c3fec5789c' or id_ == '41c24adf-2da4-4763-93f0-980d28d629f8' or id_=='7d4c12ff-a1e9-478b-9d40-5df64726ce47':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'http://kube-connect.zcode.vn/result_file/' + server + file
                header = {
                "Authorization": "token 6b31ae0a90ca4ea9a6b8911cf0d9ad7d",
                "Content-Type": "application/json",
                "Accept":"application/json, text/plain, */*"
                }
                r = requests.get(url, headers=header)
                
                url_content = r.content
                csv_file = open('./predict_csv/'+id_+'/'+file, 'wb')
                csv_file.write(url_content)
                csv_file.close()
            
            # evaluate all file and return json 
            acc_ls = []
            precision_ls = []
            recall_ls = []
            f1_score_ls = []
            time_arr = []
            memory_arr = []
            file_name =[]
            time_sum = 0
            for file in os.listdir('./trust_csv/'+id_):
                # check = evaluate_count_person('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
                # # print(check)
                # if check != True:
                #     return jsonify({'error':check})
                
                # print(evaluate_end_point('evaluate_count_person.csv'))
                # percent_correct,memory = evaluate_end_point('evaluate_count_person.csv')
                # accuracy
                acc_, precision_, recall_, f1_score_,memory = process_evaluation('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
                acc_ls.append(acc_)
                precision_ls.append(precision_)
                recall_ls.append(recall_)
                f1_score_ls.append(f1_score_)
                # memory
                memory_arr.append(memory)
                # time
                time_str = str(datetime.datetime.now() - time_current)
                time_ = datetime.time(int(time_str.split(':')[0]),int(time_str.split(':')[1]),int(time_str.split(':')[2].split('.')[0]))
                # time_format = str(time_.hour) +'h'+ str(time_.minute) +'m'+ str(time_.second) +'s'
                time_sum = time_sum + to_seconds(time_.hour,time_.minute,time_.second)
                time_arr.append(to_seconds(time_.hour,time_.minute,time_.second))
                time_current = datetime.datetime.now()
                file_name.append(file)
            
            # create json
            ob_json_ =[]
            for i in range(len(acc_ls)):
                json_ = {
                    'accuracy': acc_ls[i]*100,
                    'precision': precision_ls[i]*100,
                    'recall': recall_ls[i]*100,
                    'f1_score': f1_score_ls[i]*100,
                    'time': time_arr[i],
                    'memories': memory_arr[i],
                    'file_name':file_name[i]
                }
                ob_json_.append(json_)
            # average => json
            # print(ob_json_)
            summary = {
                'accuracy': sum(acc_ls)/len(acc_ls)*100,
                'precision': sum(precision_ls)/len(precision_ls)*100,
                'recall': sum(recall_ls)/len(recall_ls)*100,
                'f1_score': sum(f1_score_ls)/len(f1_score_ls)*100,
                'memories': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            print(summary)
            JSON = {'details':ob_json_,'summary':summary}
            return jsonify(JSON)
        
        # count car
        # elif id_== '11b4cf78-f831-4a37-8cae-b21f96e5be0d':
        #     created_folder('./predict_csv/2')
        #     for file in os.listdir('./trust_csv/1'):
        #         df = pd.read_csv('https://kube-connect.zcode.vn/result_file/server01_'+file)
        #         df.to_csv('./predict_csv/2/'+file,index=False)
        #     evaluate_count_person('1.csv','1 copy.csv')
        #     return jsonify(evaluate_end_point('evaluate_count_person.csv'))
        
        # object detection
        elif id_== '7d4c12ff-a1e9-478b-9d40-5df64726ce47':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'http://kube-connect.zcode.vn/result_file/' + server + file
                header = {
                "Authorization": "token 6b31ae0a90ca4ea9a6b8911cf0d9ad7d",
                "Content-Type": "application/json",
                "Accept":"application/json, text/plain, */*"
                }
                r = requests.get(url, headers=header)

                url_content = r.content
                csv_file = open('./predict_csv/'+id_+'/'+file, 'wb')
                csv_file.write(url_content)
                csv_file.close()
            
            # evaluate all file and return json 
            pc_ = []
            time_arr = []
            memory_arr = []
            file_name =[]
            time_sum = 0
            for file in os.listdir('./trust_csv/'+id_):
                # evaluation predicted video
                percent_correct,memory = process_evaluation('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
                # print(percent_correct,memory)
                if percent_correct == 'KeyError':
                    return jsonify({'error':memory})
                # accuracy
                pc_.append(percent_correct)
                # memory
                memory_arr.append(memory)
                # time
                time_str = str(datetime.datetime.now() - time_current)
                time_ = datetime.time(int(time_str.split(':')[0]),int(time_str.split(':')[1]),int(time_str.split(':')[2].split('.')[0]))
                # time_format = str(time_.hour) +'h'+ str(time_.minute) +'m'+ str(time_.second) +'s'
                time_sum = time_sum + to_seconds(time_.hour,time_.minute,time_.second)
                time_arr.append(to_seconds(time_.hour,time_.minute,time_.second))
                time_current = datetime.datetime.now()
                file_name.append(file)
            # create json
            ob_json_ =[]
            for i in range(len(pc_)):
                json_ = {
                    'accuracy': pc_[i],
                    'time': time_arr[i],
                    'memories': memory_arr[i],
                    'file_name':file_name[i]
                }
                ob_json_.append(json_)
            # average => json
            summary = {
                'accuracy': sum(pc_)/len(pc_),
                'memories': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            JSON = {'details':ob_json_,'summary':summary}
            return jsonify(JSON)
            # return jsonify(evaluate_detect_object('ob.csv','ob.csv'))
        
        # license plate
        elif id_ == '6b811674-56fe-40e7-882a-3414aef16b1c':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'http://kube-connect.zcode.vn/result_file/' + server + file
                header = {
                "Authorization": "token 6b31ae0a90ca4ea9a6b8911cf0d9ad7d",
                "Content-Type": "application/json",
                "Accept":"application/json, text/plain, */*"
                }
                r = requests.get(url, headers=header)

                url_content = r.content
                csv_file = open('./predict_csv/'+id_+'/'+file, 'wb')
                csv_file.write(url_content)
                csv_file.close()
            
            # evaluate all file and return json 
            pc_ = []
            time_arr = []
            memory_arr = []
            file_name = []
            time_sum = 0
            for file in os.listdir('./trust_csv/'+id_):
                percent_correct,memory = evaluate_license_plate_reg('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
                if percent_correct == 'KeyError':
                    return jsonify({'error':memory})
                # accuracy
                pc_.append(percent_correct)
                # memory
                memory_arr.append(memory)
                # time
                time_str = str(datetime.datetime.now() - time_current)
                time_ = datetime.time(int(time_str.split(':')[0]),int(time_str.split(':')[1]),int(time_str.split(':')[2].split('.')[0]))
                # time_format = str(time_.hour) +'h'+ str(time_.minute) +'m'+ str(time_.second) +'s'
                time_sum = time_sum + to_seconds(time_.hour,time_.minute,time_.second)
                time_arr.append(to_seconds(time_.hour,time_.minute,time_.second))
                time_current = datetime.datetime.now()
                file_name.append(file)
            # create json
            ob_json_ =[]
            for i in range(len(pc_)):
                json_ = {
                    'accuracy': pc_[i],
                    'time': time_arr[i],
                    'memories': memory_arr[i],
                    'file_name':file_name[i]
                }
                ob_json_.append(json_)
            # average => json
            summary = {
                'accuracy': sum(pc_)/len(pc_),
                'memories': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            JSON = {'details':ob_json_,'summary':summary}
            return jsonify(JSON)
            # return jsonify(evaluate_license_plate_reg('./video/trust.csv','./video/predict.csv'))
    except:
        return jsonify({'E':'Error'})


@app.route('/images',methods=['POST'])
@token_required
def get_images():
    folder = str(request.form.get('problem'))
    video = str(request.form.get('video'))
    frame_x = str(request.form.get('frame_x'))
    path = './static/'+folder +'/' + video + '/' + frame_x + '.jpg'
    # path1 = './static/count_people/1/0.jpg'
    return send_file(path,mimetype='image/gif')


if __name__ =='__main__':
    port_sv = int(os.environ.get('PORT', 5000))
    app.run(debug=True,host='0.0.0.0',port=port_sv)


import numpy as np
import pandas as pd
import csv
from flask import Flask,jsonify,request
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import datetime
from judge import evaluate_count_person,evaluate_end_point,evaluate_detect_object,evaluate_license_plate_reg
import requests
import time


ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)


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



# @app.route('/evaluate_count',methods=['POST'])
# def evaluate_count():
#     id_ = request.form.get('id')
#     evaluate_count_person('1.csv','1 copy.csv')
#     return jsonify(evaluate_end_point('evaluate_count_person.csv'))
    
# @app.route('/evaluate_bounding_box',methods=['POST'])
# def evaluate_bounding_box():
#     return jsonify(evaluate_detect_object('ob.csv','ob.csv'))

# @app.route('/evaluate_license_plate_reg',methods=['POST'])
# def evaluate_lp_reg():
#     return jsonify(evaluate_license_plate_reg('./video/trust.csv','./video/predict.csv'))

@app.route('/evaluate',methods=['POST'])
def evaluate():
    time_current = datetime.datetime.now()
    try:
        id_ = str(request.form.get('id'))
        server = str(request.form.get('server')) + "_"
        
        # count person and count car
        if id_ == '5dddd639-2c48-4e77-8c15-28fdb3ebe0e7' or id_ == '11b4cf78-f831-4a37-8cae-b21f96e5be0d':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'https://kube-connect.zcode.vn/result_file/' + server + file
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
            time_sum = 0
            for file in os.listdir('./trust_csv/'+id_):
                check = evaluate_count_person('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
                # print(check)
                if check != True:
                    return jsonify({'error':check})
                
                # print(evaluate_end_point('evaluate_count_person.csv'))
                percent_correct,memory = evaluate_end_point('evaluate_count_person.csv')
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
            
            # create json
            ob_json_ =[]
            for i in range(len(pc_)):
                json_ = {
                    'accuracy': pc_[i],
                    'time': time_arr[i],
                    'memory': memory_arr[i]
                }
                ob_json_.append(json_)
            # average => json
            summary = {
                'accuracy': sum(pc_)/len(pc_),
                'memory': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            JSON = {'detail':ob_json_,'summary':summary}
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
        elif id_== 'ec0cb7f9-9a70-47d0-9c4d-f84f124c3ecb':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'https://kube-connect.zcode.vn/result_file/' + server + file
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
            time_sum = 0
            for file in os.listdir('./trust_csv/'+id_):
                # evaluation predicted video
                percent_correct,memory = evaluate_detect_object('./trust_csv/'+id_+'/'+file,'./predict_csv/'+id_+'/'+file)
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
            
            # create json
            ob_json_ =[]
            for i in range(len(pc_)):
                json_ = {
                    'accuracy': pc_[i],
                    'time': time_arr[i],
                    'memory': memory_arr[i]
                }
                ob_json_.append(json_)
            # average => json
            summary = {
                'accuracy': sum(pc_)/len(pc_),
                'memory': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            JSON = {'detail':ob_json_,'summary':summary}
            return jsonify(JSON)
            # return jsonify(evaluate_detect_object('ob.csv','ob.csv'))
        
        # license plate
        elif id_ == '6d6b2ede-18ba-4a60-8966-84566b4a826c':
            # create folder
            created_folder('./predict_csv/'+id_)
            # download file predict.csv
            for file in os.listdir('./trust_csv/'+id_):
                url = 'https://kube-connect.zcode.vn/result_file/' + server + file
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
            
            # create json
            ob_json_ =[]
            for i in range(len(pc_)):
                json_ = {
                    'accuracy': pc_[i],
                    'time': time_arr[i],
                    'memory': memory_arr[i]
                }
                ob_json_.append(json_)
            # average => json
            summary = {
                'accuracy': sum(pc_)/len(pc_),
                'memory': sum(memory_arr)/len(memory_arr),
                'time': time_sum / len(time_arr)
            }
            JSON = {'detail':ob_json_,'summary':summary}
            return jsonify(JSON)
            # return jsonify(evaluate_license_plate_reg('./video/trust.csv','./video/predict.csv'))
    except:
        return jsonify({'E':'Error'})
    
if __name__ =='__main__':
    port_sv = int(os.environ.get('PORT', 5000))
    app.run(debug=True,host='0.0.0.0',port=port_sv)
    
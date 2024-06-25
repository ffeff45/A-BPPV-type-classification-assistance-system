import cv2
import os
import datetime
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt 
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder



class AviSlicingImg():

    def __init__(self):
        super().__init__()
        
        self.img_rt_np_array = []
        self.img_lt_np_array = []

    def CutImage(image):
        cut_img = image[:,40:320]
        cut_img = cut_img[:,:240]
        return cut_img
    
    def PredictUNet(array):
        unet = tf.keras.models.load_model("C:/Users/azc27/4Grade/Nystagmography/ND/model/old/240604/Unet_sharp_model_Rt_PC_BPPV.h5")
        unet.summary()
        h = unet.predict(array)
        return h
    
    def preprocessing(image):
        reimg = np.reshape(image, (240,240))
        reimg = (reimg * 255).astype(np.uint8)
        et, imthres = cv2.threshold(reimg, 0, 255, cv2.THRESH_BINARY_INV)
        contours, hier = cv2.findContours(imthres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours[1]
    
    def Ellipse(image):
        ellipse = cv2.fitEllipse(image)     
        return ellipse
    

    def SSH():
        ssh_host = '210.126.67.40'
        ssh_port = 7785
        ssh_username = 'qhdrmfdl1234'
        ssh_password = 'Wndlf7785!'

        tunnel = SSHTunnelForwarder((ssh_host, ssh_port),
                                ssh_username=ssh_username,
                                ssh_password=ssh_password,
                                remote_bind_address=('127.0.0.1', 3306))
        return tunnel
    

    def DB_Insert(sql):
        tunnel = AviSlicingImg.SSH()
        sql_hostname = '127.0.0.1'
        sql_username = 'bppv'
        sql_password = '1234'
        sql_database = 'BppvDB'

        with tunnel:
            print("== SSH Tunnel ==")
            conn = pymysql.connect(
                    host=sql_hostname, 
                    user=sql_username,
                    password=sql_password, 
                    charset="utf8",
                    db=sql_database,
                    port=tunnel.local_bind_port)
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()

    def DB_select(sql):
        tunnel = AviSlicingImg.SSH()
        sql_hostname = '127.0.0.1'
        sql_username = 'bppv'
        sql_password = '1234'
        sql_database = 'BppvDB'
        
        with tunnel:
            print("== SSH Tunnel ==")
            conn = pymysql.connect(
                    host=sql_hostname, 
                    user=sql_username,
                    password=sql_password, 
                    charset="utf8",
                    db=sql_database,
                    port=tunnel.local_bind_port)
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            print(sql)
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()

        df = pd.DataFrame(result)
        df.head()
        return df

    def img_slice_save(self, path, date):

        video = cv2.VideoCapture(path) #'' 사이에 사용할 비디오 파일의 경로 및 이름을 넣어주도록 함

        V_name = os.path.basename(path)
        sql_imgid = f"SELECT videoid FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
        id_df = AviSlicingImg.DB_select(sql_imgid)

        #변수 이름 수정 바람 
        row_1 = id_df.iloc[0]
        v_id =str(row_1["videoid"])
        n = v_id.zfill(4)

        length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_r_array = []
        frame_l_array = []
        
        if not video.isOpened():
            print("Could not Open :", path)
            exit(0)
            
        for i in range(length):
            num = '{0:04d}'.format(i)
            ret, frame = video.read() 
            frame_col = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if ret:
                frame_rt = frame_col[:, :161]
                frame_r = cv2.resize(frame_rt, (320, 240))

                r_image_name = f"{n}_{V_name}_R_{num}"
                
                frame_lt = frame_col[:, 161:]
                frame_l = cv2.resize(frame_lt, (320, 240))

                L_image_name = f"{n}_{V_name}_L_{num}"

                frame_r_array.append(AviSlicingImg.CutImage(frame_r))
                frame_l_array.append(AviSlicingImg.CutImage(frame_l))

                

            else:
                print("NOpe")
                
        self.img_rt_np_array = np.array(frame_r_array)
        self.img_lt_np_array = np.array(frame_l_array)
        
        # np.save("frame_rt",self.img_rt_np_array)
        # np.save("frame_lt",self.img_lt_np_array) #DB 넘어가는 코드 작성되면 사라져용 확인용
        
        video.release()
        img_l = AviSlicingImg.PredictUNet(self.img_lt_np_array)
        for i in range(len(img_l)):
            bppv_img = img_l[i]
            list = AviSlicingImg.preprocessing(bppv_img)
            elii = AviSlicingImg.Ellipse(list)
            print(elii)
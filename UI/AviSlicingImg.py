import cv2
import os
import sys
import pickle
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
import tensorflow as tf
import matplotlib.pyplot as plt 
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager



class AviSlicingImg():

    def __init__(self):
        super().__init__()

    def CutImage(image):
        cut_img = image[:, 40:280]
        img = np.array(cut_img)
        return img/255
    
    def PredictUNet(array):
        unet = tf.keras.models.load_model("Unet_sharp_model_Rt_Geo_BPPV.h5")
        # unet.summary()
        h = unet.predict(array)
        return h
    
    def preprocessing(image):
        reimg = np.reshape(image, (240, 240))
        reimg = (reimg * 255).astype(np.uint8)
        _, imthres = cv2.threshold(reimg, 0, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(imthres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # print(contours)
        _, _, select_contours = AviSlicingImg.find_largest_2d_array(contours)
        return contours[select_contours]
    
    def find_largest_2d_array(arr):
        max_elements = -1
        largest_2d_array = None
        largest_index = -1
        
        for i, sub_array in enumerate(arr):
            element_count = sum(len(row) for row in sub_array)
            if element_count > max_elements:
                max_elements = element_count
                largest_2d_array = sub_array
                largest_index = i
        
        return largest_2d_array, max_elements, largest_index

    def Ellipse(image):
        return cv2.fitEllipse(image)
    
    @contextmanager
    def SSH():
        ssh_host = '210.126.67.40'
        ssh_port = 7785
        ssh_username = 'qhdrmfdl1234'
        ssh_password = 'Wndlf7785!'
        
        tunnel = SSHTunnelForwarder((ssh_host, ssh_port),
                                    ssh_username=ssh_username,
                                    ssh_password=ssh_password,
                                    remote_bind_address=('127.0.0.1', 3306))
        tunnel.start()
        try:
            yield tunnel
        finally:
            tunnel.stop()
    

    def DB_select(tunnel, sql):
        sql_hostname = '127.0.0.1'
        sql_username = 'bppv'
        sql_password = '1234'
        sql_database = 'BppvDB'

        conn = pymysql.connect(
                host=sql_hostname, 
                user=sql_username,
                password=sql_password, 
                charset="utf8",
                db=sql_database,
                port=tunnel.local_bind_port)

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return pd.DataFrame(result)
        finally:
            conn.close()

    def DB_Insert(tunnel, sql, params):
        sql_hostname = '127.0.0.1'
        sql_username = 'bppv'
        sql_password = '1234'
        sql_database = 'BppvDB'

        conn = pymysql.connect(
                host=sql_hostname, 
                user=sql_username,
                password=sql_password, 
                charset="utf8",
                db=sql_database,
                port=tunnel.local_bind_port)
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
        finally:
            conn.close()

    def img_slice_save(self, path, date):
        video = cv2.VideoCapture(path) #'' 사이에 사용할 비디오 파일의 경로 및 이름을 넣어주도록 함

        if not video.isOpened():
            print("Could not open:", path)
            return
        
        V_name = os.path.basename(path)
        with AviSlicingImg.SSH() as tunnel:
            sql_imgid = f"SELECT videoid FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_df = AviSlicingImg.DB_select(tunnel, sql_imgid)

            row_1 = id_df.iloc[0]
            v_id = str(row_1["videoid"]).zfill(4)

            length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_r_array = []
            frame_l_array = []
            
            for i in range(length):
                ret, frame = video.read() 
                if not ret:
                    break
                frame_col = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_rt = cv2.resize(frame_col[:, :161], (320, 240))
                frame_lt = cv2.resize(frame_col[:, 161:], (320, 240))

                frame_r_array.append(AviSlicingImg.CutImage(frame_rt))
                frame_l_array.append(AviSlicingImg.CutImage(frame_lt))

            img_rt_np_array = np.array(frame_r_array)
            img_lt_np_array = np.array(frame_l_array)

            rt_random_indices = np.random.choice(img_rt_np_array.shape[0], 5, replace=False)
            selected_rt_arrays = img_rt_np_array[rt_random_indices]

            sql= "INSERT INTO Images (imageid, imagenparray) VALUES (%s, %s);"

            for i, array in enumerate(selected_rt_arrays):
                num_1 = f'{i+1:04d}'
                frame_rt_array_binary = pickle.dumps(array)

                R_image_name = f"{v_id}_{V_name}_R_{num_1}"

                AviSlicingImg.DB_Insert(tunnel, sql, (R_image_name, frame_rt_array_binary))
            
            lt_random_indices = np.random.choice(img_lt_np_array.shape[0], 5, replace=False)
            selected_lt_arrays = img_lt_np_array[lt_random_indices]

            for i, array in enumerate(selected_lt_arrays):
                num_1 = f'{i+1:04d}'
                frame_l_array_binary = pickle.dumps(array)

                L_image_name = f"{v_id}_{V_name}_L_{num_1}"

                AviSlicingImg.DB_Insert(tunnel, sql, (L_image_name, frame_l_array_binary))
            

            img_rt_np_array_1 = np.reshape(img_rt_np_array, (len(img_rt_np_array), 240, 240, 1))
            img_lt_np_array_1 = np.reshape(img_lt_np_array, (len(img_lt_np_array), 240, 240, 1))

            img_R = AviSlicingImg.PredictUNet(img_rt_np_array_1)
            img_L = AviSlicingImg.PredictUNet(img_lt_np_array_1)

            sql= "INSERT INTO Pupils (imageid, x, y, max_distance, min_distance, slope) VALUES (%s, %s, %s, %s, %s, %s);"


            for i in range(len(img_R)):
                num_2 = f'{i+1:04d}'
                R_image_name_2 = f"{v_id}_{V_name}_R_{num_2}"
                
                bppv_img = img_R[i]

                list_contour = AviSlicingImg.preprocessing(bppv_img)
                elii = AviSlicingImg.Ellipse(list_contour)

                value1 = elii[0][0]
                value2 = elii[0][1]
                value3 = elii[1][0]
                value4 = elii[1][1]
                value5 = elii[2]
                AviSlicingImg.DB_Insert(tunnel, sql, (R_image_name_2, value1, value2, value3, value4, value5))
            
            print(2)

            for i in range(len(img_L)):
                num_2 = f'{i+1:04d}'
                L_image_name_2 = f"{v_id}_{V_name}_L_{num_2}"
                print(num_2)

                bppv_img = img_L[i]

                list_contour = AviSlicingImg.preprocessing(bppv_img)
                elii = AviSlicingImg.Ellipse(list_contour)

                value1 = elii[0][0]
                value2 = elii[0][1]
                value3 = elii[1][0]
                value4 = elii[1][1]
                value5 = elii[2]
                AviSlicingImg.DB_Insert(tunnel, sql, (L_image_name_2, value1, value2, value3, value4, value5))
        
        # np.save("frame_rt",self.img_rt_np_array)
        # np.save("frame_lt",self.img_lt_np_array) #DB 넘어가는 코드 작성되면 사라져용 확인용
        
        video.release()
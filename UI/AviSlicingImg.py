import cv2
import os
import sys
import time
import pickle
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
import tensorflow as tf
import matplotlib.pyplot as plt 
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
import datetime
import matplotlib.dates as mdates



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
        _, _, select_contours = AviSlicingImg.find_largest_2d_array(contours)
        # print(select_contours)
        list_contour = contours[select_contours]
        contour_re = list_contour.reshape(list_contour.shape[0],list_contour.shape[2])
        return contour_re
    
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

    # def folder(res_id):
    #     user_p = os.getcwd()
    #     folrder_o = f"\\Original\\{res_id}"
    #     folder_result = f"\\Result\\{res_id}"

    #     r_o_p = os.makedirs(user_p+folrder_o+'\\Eye_R')
    #     l_o_p = os.makedirs(user_p+folrder_o+'\\Eye_L')
    #     res_r_p = os.makedirs(user_p+folder_result+'\\Eye_R')
    #     res_l_p = os.makedirs(user_p+folder_result+'\\Eye_L')
    #     res_eye_t_p = os.makedirs(user_p+folder_result+'\\eyetrace')

    #     r_o_path = user_p+folrder_o+'\\Eye_R'
    #     l_o_path = user_p+folrder_o+'\\Eye_L'
    #     r_res_path = user_p+folder_result+'\\Eye_R'
    #     l_res_path = user_p+folder_result+'\\Eye_L'
    #     res_eye_trace = user_p+folder_result+'\\eyetrace'

    #     return r_o_path, l_o_path, r_res_path, l_res_path, res_eye_trace

    def img_slice_save(self, path, date, progress_callback=None):
        video = cv2.VideoCapture(path) #'' 사이에 사용할 비디오 파일의 경로 및 이름을 넣어주도록 함

        if not video.isOpened():
            print("Could not open:", path)
            return
        
        V_name = os.path.basename(path)
        with AviSlicingImg.SSH() as tunnel:
            sql_imgid = f"SELECT videoid,videoname FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_df = AviSlicingImg.DB_select(tunnel, sql_imgid)                    
            row_1 = id_df.iloc[0]      
            v_id = str(row_1["videoid"]).zfill(4)
            res_id = v_id +"_"+ str(row_1["videoname"])  

            AviSlicingImg.folder(res_id)

            length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_r_array = []
            frame_l_array = []

            if progress_callback:
                progress_callback(20)  # 첫 번째 단계 완료 후 20% 진행
            
            for i in range(length):
                ret, frame = video.read() 
                if not ret:
                    break
                frame_col = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_rt = cv2.resize(frame_col[:, :161], (320, 240))
                frame_lt = cv2.resize(frame_col[:, 161:], (320, 240))

                frame_r_array.append(AviSlicingImg.CutImage(frame_rt))
                frame_l_array.append(AviSlicingImg.CutImage(frame_lt))

                if progress_callback:
                    progress_percent = int((i + 1) / length * 20)  # 두 번째 단계 완료 후 40% 진행
                    progress_callback(progress_percent)

            img_rt_np_array = np.array(frame_r_array)
            img_lt_np_array = np.array(frame_l_array)

            img_r_o = img_rt_np_array[0]
            img_l_o = img_lt_np_array[0]


            new_size = (240,240)
            # VideoWriter 객체 생성 (코덱 설정)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            out_r_o = cv2.VideoWriter(r_o_path, fourcc, fps, new_size)

            sql= "INSERT INTO Images (imageid, imagenparray) VALUES (%s, %s);"

            rt_random_indices = np.random.choice(img_rt_np_array.shape[0], 5, replace=False)
            selected_rt_arrays = img_rt_np_array[rt_random_indices]

            for i, array in enumerate(selected_rt_arrays):
                num_1 = f'{i+1:04d}'
                frame_rt_array_binary = pickle.dumps(array)

                R_image_name = f"{v_id}_{V_name}_R_{num_1}"

                AviSlicingImg.DB_Insert(tunnel, sql, (R_image_name, frame_rt_array_binary))
                if progress_callback:
                    progress_percent = 20 + int((i + 1) / len(selected_rt_arrays) * 20)  
                    progress_callback(progress_percent)
            
            lt_random_indices = np.random.choice(img_lt_np_array.shape[0], 5, replace=False)
            selected_lt_arrays = img_lt_np_array[lt_random_indices]

            for i, array in enumerate(selected_lt_arrays):
                num_1 = f'{i+1:04d}'
                frame_l_array_binary = pickle.dumps(array)

                L_image_name = f"{v_id}_{V_name}_L_{num_1}"

                AviSlicingImg.DB_Insert(tunnel, sql, (L_image_name, frame_l_array_binary))
                if progress_callback:
                    progress_percent = 40 + int((i + 1) / len(selected_lt_arrays) * 20)  
                    progress_callback(progress_percent)
            

            img_rt_np_array_1 = np.reshape(img_rt_np_array, (len(img_rt_np_array), 240, 240, 1))
            img_lt_np_array_1 = np.reshape(img_lt_np_array, (len(img_lt_np_array), 240, 240, 1))

            img_R = AviSlicingImg.PredictUNet(img_rt_np_array_1)
            print("Fin R")
            img_L = AviSlicingImg.PredictUNet(img_lt_np_array_1)
            print("Fin L")

            sql= "INSERT INTO Pupils (imageid, x, y, max_distance, min_distance, slope) VALUES (%s, %s, %s, %s, %s, %s);"


            for i in range(len(img_R)):
                num_2 = f'{i+1:04d}'
                R_image_name_2 = f"{v_id}_{V_name}_R_{num_2}"
                
                bppv_img = img_R[i]

                list_contour = AviSlicingImg.preprocessing(bppv_img)
                re_list_contour = np.delete(list_contour, [0,1,-2,-1] , axis = 0)
                if len(re_list_contour) < 5:
                    print(num_2)
                    continue
                elii = AviSlicingImg.Ellipse(re_list_contour)

                value1 = elii[0][0]
                value2 = elii[0][1]
                value3 = elii[1][0]
                value4 = elii[1][1]
                value5 = elii[2]
                AviSlicingImg.DB_Insert(tunnel, sql, (R_image_name_2, value1, value2, value3, value4, value5))
                if progress_callback:
                    progress_percent = 60 + int((i + 1) / len(img_R) * 20)  
                    progress_callback(progress_percent)
                time.sleep(0.001)

            for i in range(len(img_L)):
                num_2 = f'{i+1:04d}'
                L_image_name_2 = f"{v_id}_{V_name}_L_{num_2}"

                bppv_img = img_L[i]

                list_contour = AviSlicingImg.preprocessing(bppv_img)
                re_list_contour = np.delete(list_contour, [0,1,-2,-1] , axis = 0)
                if len(re_list_contour) < 5:
                    print(num_2)
                    continue
                elii = AviSlicingImg.Ellipse(re_list_contour)

                value1 = elii[0][0]
                value2 = elii[0][1]
                value3 = elii[1][0]
                value4 = elii[1][1]
                value5 = elii[2]
                print(num_2,":",value1,value2,value3,value4,value5)
                AviSlicingImg.DB_Insert(tunnel, sql, (L_image_name_2, value1, value2, value3, value4, value5))
                if progress_callback:
                    progress_percent = 80 + int((i + 1) / len(img_L) * 20)  
                    progress_callback(progress_percent)
                time.sleep(0.001)
        
        # np.save("frame_rt",self.img_rt_np_array)
        # np.save("frame_lt",self.img_lt_np_array) #DB 넘어가는 코드 작성되면 사라져용 확인용
        
        video.release()


    def center_point(self, path, date,fps,frame): 
        # path = "C:\\Users\\kreyu\\Desktop\\4grade\\NDT\\ND\\data\\Rt_Apo_BPPV_Short.mp4"
        V_name = os.path.basename(path)
        # fps = AviSlicingImg.get(cv2.CAP_PROP_FPS)
        # date = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        # fps = 24
        

        with AviSlicingImg.SSH() as tunnel:
            sql_imgid = f"SELECT videoid,videoname FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_df = AviSlicingImg.DB_select(tunnel, sql_imgid)                    
            row_1 = id_df.iloc[0]      
            v_id = str(row_1["videoid"]).zfill(4)
            res_id = v_id +"_"+ str(row_1["videoname"])   
               
            
            sql_R_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_R_%' ;"
            sql_L_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_L_%' ;"
        
            df_R_pupils = AviSlicingImg.DB_select(tunnel, sql_R_pupils)
            df_L_pupils = AviSlicingImg.DB_select(tunnel, sql_L_pupils)
            # print(df_R_pupils)

            t_d= []

            for frame in range(int(frame)):
                duration = frame / fps if fps > 0 else 0  
                td = datetime.timedelta(seconds=duration)
                stime = str(td.total_seconds())
                t_d.append(stime)
            
            # print(t_d)

            df_R_pupils['time'] = pd.to_datetime(t_d, format='%S.%f', errors='raise')
            df_L_pupils['time'] = pd.to_datetime(t_d, format='%S.%f', errors='raise')
            # print(df_R_pupils)
            # print(df_L_pupils)

            R_pupils = df_R_pupils[[df_R_pupils.columns[0],df_R_pupils.columns[1]]].to_numpy()
            L_pupils = df_L_pupils[[df_L_pupils.columns[0],df_L_pupils.columns[1]]].to_numpy()           
            
            user_p = "C:\\Users\\kreyu\\Desktop\\4grade\\NDT\\ND" #본인 경로로 변경
            folrder_o = f"\\Original\\{res_id}"
            folder_result = f"\\Result\\{res_id}"
            
            r_o_p = os.makedirs(user_p+folrder_o+'\\Eye_R')
            l_o_p = os.makedirs(user_p+folrder_o+'\\Eye_L')
            res_r_p = os.makedirs(user_p+folder_result+'\\Eye_R')
            res_l_p = os.makedirs(user_p+folder_result+'\\Eye_L')
            res_eye_t_p = os.makedirs(user_p+folder_result+'\\eyetrace')

            r_o_path = user_p+folrder_o+'\\Eye_R'
            l_o_path = user_p+folrder_o+'\\Eye_L'
            r_res_path = user_p+folder_result+'\\Eye_R'
            l_res_path = user_p+folder_result+'\\Eye_L'
            res_eye_trace = user_p+folder_result+'\\eyetrace'
            print(r_o_path,l_o_path,r_res_path,l_res_path)
        

            df_R_pupils.to_csv('./R_point.csv',index=False)
            df_L_pupils.to_csv('./L_point.csv',index=False)
            row_1.to_csv('./row.csv',index=False)
            
            
        AviSlicingImg.plot_point(df_R_pupils,df_L_pupils,res_id)
        AviSlicingImg.bppv_plot(path,R_pupils,L_pupils,r_o_path,l_o_path,r_res_path,l_res_path)

    def plot_point(data_r, data_l, res_id) : 
        fig = plt.figure()           
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        # print(data_r, data_l, res_id, res_p)
        formatter = mdates.DateFormatter('%S')

        ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax1.xaxis.set_major_formatter(formatter) 

        ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax2.xaxis.set_major_formatter(formatter) 


        ax1.set_ylim(0,320)
        ax1.set_ylabel(ylabel = 'X_point')
        
        ax2.set_ylim(0,240)
        
        ax2.set_ylabel(ylabel = 'Y_point')
        ax2.set_xlabel(xlabel = 'time(s)')

        ax1.plot(data_l['time'], data_l['x'] ,c = "g" ,label = 'Eye_L')
        ax1.plot(data_r['time'], data_r['x'],c = "r" ,label = 'Eye_R')
        ax2.plot(data_l['time'], data_l['y'],c = "g" ,label = 'Eye_L')
        ax2.plot(data_r['time'], data_r['y'],c = "r" ,label = 'Eye_R')
        ax1.legend()
        ax2.legend()

        fig.savefig(f"C:\\Users\\kreyu\\Desktop\\4grade\\NDT\\ND\\Result\\{res_id}\\eyetrace\\{res_id}.png")

        return fig
        

    def bppv_plot(path, data_r, data_l,r_o_p,l_o_p,res_r_p,res_l_p):
        # print(path, data_r, data_l,r_o_p,l_o_p,res_r_p,res_l_p)
        video = cv2.VideoCapture(path)       

        if not video.isOpened():
            print("Could not open:", path)

        fps = video.get(cv2.CAP_PROP_FPS)
            
        length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_o_r_array = []
        frame_o_l_array = []
        

        for i in range(length):
            ret, frame = video.read() 
            if not ret:
                print("Nope")
                break
            frame_o_r_array.append(frame[:, :161])
            frame_o_l_array.append(frame[:, 161:])
            
        img_o_r = cv2.resize(frame_o_r_array[0],(240,240))
        img_o_l = cv2.resize(frame_o_l_array[0],(240,240))

        img_u_r = cv2.resize(frame_o_r_array[0],(240,240))
        img_u_l = cv2.resize(frame_o_l_array[0],(240,240))

        new_size = (240,240)
        # VideoWriter 객체 생성 (코덱 설정)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_r_o = cv2.VideoWriter(r_o_p, fourcc, fps, new_size)
        out_l_o = cv2.VideoWriter(l_o_p, fourcc, fps, new_size)
        out_r_res = cv2.VideoWriter(res_r_p, fourcc, fps, new_size)
        out_l_res = cv2.VideoWriter(res_l_p, fourcc, fps, new_size)
        
        #elli_list DB에서 알아서 x,y 가져와서 value1, value2에 넣으시오.
        # elli_list 대신 df len 쓰면 될 듯
        
        for i in range(len(data_r)):
            value1 = int(data_r[0][0])
            value2 = int(data_r[0][1])
            cv2.circle(img_u_r,(value1,value2), 2, 255, -1)
            out_r_res.write(img_u_r)

        out_r_res.release()

        for i in range(len(data_l)):
            value1 = int(data_l[0][0])
            value2 = int(data_l[0][1])
            cv2.circle(img_u_l,(value1,value2), 2, 255, -1)
            out_l_res.write(img_u_l)

        out_l_res.release()
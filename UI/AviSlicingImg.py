import cv2
import os
import sys
import time
import pickle
import getpass
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

    def CutImage(image):
        cut_img = image[:, 40:280]
        img = np.array(cut_img)
        return img.astype(np.uint8), img/255
    
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

    def folder(res_id):
        res_id = res_id[:-4]
        username = getpass.getuser()
        user_path = os.path.join("C:\\Users", username)

        ND_path = os.path.join(user_path,'ND')

        Original_path = os.path.join(ND_path,'Original',res_id)
        Result_path = os.path.join(ND_path,'Result',res_id)

        r_o_path = os.path.join(Original_path,'Eye_R.mp4')
        l_o_path = os.path.join(Original_path,'Eye_L.mp4')
        r_res_path = os.path.join(Result_path,'Eye_R.mp4')
        l_res_path = os.path.join(Result_path,'Eye_L.mp4')


        if not os.path.exists(ND_path):
            os.makedirs(ND_path)

        if not os.path.exists(Original_path):
            os.makedirs(Original_path)
        
        if not os.path.exists(Result_path):
            os.makedirs(Result_path)
        

        return r_o_path, l_o_path, r_res_path, l_res_path, Result_path
    
    def read_and_cut_frames(filepath, r_o_path, l_o_path, progress_callback=None):
        new_size = (240,240)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        cap = cv2.VideoCapture(filepath)

        if not cap.isOpened():
            print("Could not open:", filepath)
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        out_r_o = cv2.VideoWriter(r_o_path, fourcc, fps, new_size)
        out_l_o = cv2.VideoWriter(l_o_path, fourcc, fps, new_size)


        frame_r_array = []
        frame_l_array = []

        for f in range(total_frames):
            ret, frame = cap.read()

            if not ret:
                print("Nope")
                break

            frame_col = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_r = cv2.resize(frame_col[:, :161], (320, 240))
            frame_l = cv2.resize(frame_col[:, 161:], (320, 240))

            cut_r, r_img_array = AviSlicingImg.CutImage(frame_r)
            cut_l, l_img_array = AviSlicingImg.CutImage(frame_l)


            cut_r_img_1 = cv2.cvtColor(cut_r, cv2.COLOR_GRAY2RGB)
            cut_l_img_1 = cv2.cvtColor(cut_l, cv2.COLOR_GRAY2RGB)

            if f == 0:
                img_r_o = cv2.cvtColor(cut_r, cv2.COLOR_GRAY2RGB)
                img_l_o = cv2.cvtColor(cut_l, cv2.COLOR_GRAY2RGB)

            out_r_o.write(cut_r_img_1)
            out_l_o.write(cut_l_img_1)      

            frame_r_array.append(r_img_array)
            frame_l_array.append(l_img_array)

            if progress_callback:
                progress_callback(20 * f / total_frames)

        cap.release()
        out_r_o.release()
        out_l_o.release()

        return fps, total_frames, frame_r_array, frame_l_array, img_r_o, img_l_o

    def predict_and_preprocess(frame_r_array, frame_l_array, progress_callback=None):

        frame_r_array_np = np.array(frame_r_array)
        frame_l_array_np = np.array(frame_l_array)

        frame_r_array_np_reshape = np.reshape(frame_r_array_np, (len(frame_r_array_np), 240, 240, 1))
        frame_l_array_np_rehsape = np.reshape(frame_l_array_np, (len(frame_l_array_np), 240, 240, 1))
        
        pred_r = AviSlicingImg.PredictUNet(frame_r_array_np_reshape)
        for i in range(10):
            if progress_callback:
                progress_callback(40+i)

        pred_l = AviSlicingImg.PredictUNet(frame_l_array_np_rehsape)
        for i in range(10):
            if progress_callback:
                progress_callback(50+i)

        return pred_r, pred_l

    def process_ellips(tunnel, sql, img_array, v_id, V_name, side, progress_start, progress_end, progress_callback=None):

        for i in range(len(img_array)):
            num_2 = f'{i+1:04d}'
            image_name = f"{v_id}_{V_name}_{side}_{num_2}"

            bppv_img = img_array[i]

            list_contour = AviSlicingImg.preprocessing(bppv_img)
            re_list_contour = np.delete(list_contour, [0,1,-2,-1], axis=0)

            if len(re_list_contour) < 5:
                value1 = 0 
                value2 = 0
                value3 = 0
                value4 = 0
                value5 = 0
                AviSlicingImg.DB_Insert(tunnel, sql, (image_name, value1, value2, value3, value4, value5))
                continue
            
            elli = AviSlicingImg.Ellipse(re_list_contour)

            value1 = elli[0][0]
            value2 = elli[0][1]
            value3 = elli[1][0]
            value4 = elli[1][1]
            value5 = elli[2]

            AviSlicingImg.DB_Insert(tunnel, sql, (image_name, value1, value2, value3, value4, value5))

            if progress_callback:
                progress_percent = progress_start + int((i + 1) / len(img_array) * (progress_end - progress_start))
                progress_callback(progress_percent)

            time.sleep(0.001)

    def time_list(fps, frame):
        t_d= []

        for frame in range(int(frame)):
            duration = frame / fps if fps > 0 else 0  
            td = datetime.timedelta(seconds=duration)
            stime = str(td.total_seconds())
            t_d.append(stime)
        return t_d
    
    def plot_point(data_r, data_l, res_id, path, progress_callback=None): 
        fig = plt.figure()
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        formatter = mdates.DateFormatter('%S')

        ax1.set_ylim(0,320)
        ax1.set_ylabel(ylabel = 'X_point')
        ax1.set_xlabel(xlabel = 'time(s)')
        ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax1.xaxis.set_major_formatter(formatter) 


        ax2.set_ylim(0,240)
        ax2.set_ylabel(ylabel = 'Y_point')
        ax2.set_xlabel(xlabel = 'time(s)')
        ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax2.xaxis.set_major_formatter(formatter) 

        ax1.plot('time', 'x', data = data_l, c = "g", label = 'Eye_L')
        ax1.plot('time', 'x', data = data_r, c = "r", label = 'Eye_R')
        
        ax2.plot('time', 'y', data = data_l, c = "g", label = 'Eye_L')
        ax2.plot('time', 'y', data = data_r, c = "r", label = 'Eye_R')

        ax1.legend()
        ax2.legend()

        img_path = os.path.join(path, f"eyetrace_{res_id}.png")

        fig.savefig(img_path)

        for i in range(10):
            if progress_callback:
                progress_callback(80+i)

    def bppv_plot(fps, data_r, data_l, df_r, df_l, res_r_p, res_l_p, progress_callback=None):
        
        new_size = (240,240)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        out_r_res = cv2.VideoWriter(res_r_p, fourcc, fps, new_size)
        out_l_res = cv2.VideoWriter(res_l_p, fourcc, fps, new_size)
        
        #elli_list DB에서 알아서 x,y 가져와서 value1, value2에 넣으시오.
        # elli_list 대신 df len 쓰면 될 듯
        
        for i in range(len(df_r)):
            value1 = int(df_r["x"][i])
            value2 = int(df_r["y"][i])
            cv2.circle(data_r,(value1,value2), 2, 255, -1)
            out_r_res.write(data_r)
            if progress_callback:
                progress_callback(90 + int((i + 1) / len(df_r) * 5))

        out_r_res.release()

        for i in range(len(df_l)):
            value1 = int(df_l["x"][i])
            value2 = int(df_l["y"][i])
            cv2.circle(data_l,(value1,value2), 2, 255, -1)
            out_l_res.write(data_l)
            if progress_callback:
                progress_callback(95 + int((i + 1) / len(df_l) * 5))

        out_l_res.release()


    def img_slice_save(self, path, date, progress_callback=None):

        V_name = os.path.basename(path)

        with AviSlicingImg.SSH() as tunnel:

            sql_imginfo = f"SELECT videoid FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_info = AviSlicingImg.DB_select(tunnel, sql_imginfo)

            id_info_row = id_info.iloc[0]      
            v_id = str(id_info_row["videoid"]).zfill(4)
            res_id = v_id +"_"+ V_name

            r_o_path, l_o_path, r_res_path, l_res_path, eyetrace_path = AviSlicingImg.folder(res_id)

            fps, total_frames, frame_r_array, frame_l_array, img_r_o, img_l_o = AviSlicingImg.read_and_cut_frames(path, r_o_path, l_o_path, progress_callback)

            pred_r, pred_l = AviSlicingImg.predict_and_preprocess(frame_r_array, frame_l_array)

            sql_insert_pupils = "INSERT INTO Pupils (imageid, x, y, max_distance, min_distance, slope) VALUES (%s, %s, %s, %s, %s, %s);"
            AviSlicingImg.process_ellips(tunnel, sql_insert_pupils, pred_r, v_id, V_name, "R", 60, 70, progress_callback)
            AviSlicingImg.process_ellips(tunnel, sql_insert_pupils, pred_l, v_id, V_name, "L", 70, 80, progress_callback)


            sql_R_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_R_%';"
            sql_L_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_L_%';"

            df_R_pupils = AviSlicingImg.DB_select(tunnel, sql_R_pupils)
            df_L_pupils = AviSlicingImg.DB_select(tunnel, sql_L_pupils)

            t_list = AviSlicingImg.time_list(fps, total_frames)
            df_R_pupils['time'] = pd.to_datetime(t_list, format='%S.%f', errors='raise')
            df_L_pupils['time'] = pd.to_datetime(t_list, format='%S.%f', errors='raise')


            AviSlicingImg.plot_point(df_R_pupils, df_L_pupils,res_id, eyetrace_path, progress_callback)
            AviSlicingImg.bppv_plot(fps, img_r_o, img_l_o, df_R_pupils, df_L_pupils, r_res_path, l_res_path, progress_callback)

            cv2.destroyAllWindows()


            # sql= "INSERT INTO Images (imageid, imagenparray) VALUES (%s, %s);"

            # rt_random_indices = np.random.choice(img_rt_np_array.shape[0], 5, replace=False)
            # selected_rt_arrays = img_rt_np_array[rt_random_indices]

            # for i, array in enumerate(selected_rt_arrays):
            #     num_1 = f'{i+1:04d}'
            #     frame_rt_array_binary = pickle.dumps(array)

            #     R_image_name = f"{v_id}_{V_name}_R_{num_1}"

            #     AviSlicingImg.DB_Insert(tunnel, sql, (R_image_name, frame_rt_array_binary))
            #     if progress_callback:
            #         progress_percent = 20 + int((i + 1) / len(selected_rt_arrays) * 20)  
            #         progress_callback(progress_percent)
            
            # lt_random_indices = np.random.choice(img_lt_np_array.shape[0], 5, replace=False)
            # selected_lt_arrays = img_lt_np_array[lt_random_indices]

            # for i, array in enumerate(selected_lt_arrays):
            #     num_1 = f'{i+1:04d}'
            #     frame_l_array_binary = pickle.dumps(array)

            #     L_image_name = f"{v_id}_{V_name}_L_{num_1}"

            #     AviSlicingImg.DB_Insert(tunnel, sql, (L_image_name, frame_l_array_binary))
            #     if progress_callback:
            #         progress_percent = 40 + int((i + 1) / len(selected_lt_arrays) * 20)  
            #         progress_callback(progress_percent)

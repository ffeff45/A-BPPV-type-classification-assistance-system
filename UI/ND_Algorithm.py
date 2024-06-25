import cv2
import os
import sys
import time
import pickle
import shutil
import getpass
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt 
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
import datetime
import matplotlib.dates as mdates



class ND():

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
        _, _, select_contours = ND.find_largest_2d_array(contours)
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

            cut_r, r_img_array = ND.CutImage(frame_r)
            cut_l, l_img_array = ND.CutImage(frame_l)


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
        
        pred_r = ND.PredictUNet(frame_r_array_np_reshape)
        for i in range(10):
            if progress_callback:
                progress_callback(20+i)

        pred_l = ND.PredictUNet(frame_l_array_np_rehsape)
        for i in range(10):
            if progress_callback:
                progress_callback(30+i)

        return pred_r, pred_l

    def process_ellips(tunnel, sql, img_array, v_id, V_name, side, progress_start, progress_end, progress_callback=None):

        for i in range(len(img_array)):
            num_2 = f'{i+1:04d}'
            image_name = f"{v_id}_{V_name}_{side}_{num_2}"

            bppv_img = img_array[i]

            list_contour = ND.preprocessing(bppv_img)
            re_list_contour = np.delete(list_contour, [0,1,-2,-1], axis=0)

            if len(re_list_contour) < 5:
                value1 = 0 
                value2 = 0
                value3 = 0
                value4 = 0
                value5 = 0
                ND.DB_Insert(tunnel, sql, (image_name, value1, value2, value3, value4, value5))
                continue
            
            elli = ND.Ellipse(re_list_contour)

            value1 = elli[0][0]
            value2 = elli[0][1]
            value3 = elli[1][0]
            value4 = elli[1][1]
            value5 = elli[2]

            ND.DB_Insert(tunnel, sql, (image_name, value1, value2, value3, value4, value5))

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
        print(1)
        fig1 = plt.figure()
        fig2 = plt.figure()
        fig3 = plt.figure()
        fig4 = plt.figure()

        fig1, ax1 = plt.subplots( )
        fig2, ax2 = plt.subplots( )
        fig3, ax3 = plt.subplots( )
        fig4, ax4 = plt.subplots( )
        formatter = mdates.DateFormatter('%S')
        print(2)
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

        ax3.set_ylim(0,320)
        ax3.set_ylabel(ylabel = 'X_point')
        ax3.set_xlabel(xlabel = 'time(s)')
        ax3.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax3.xaxis.set_major_formatter(formatter) 


        ax4.set_ylim(0,240)
        ax4.set_ylabel(ylabel = 'Y_point')
        ax4.set_xlabel(xlabel = 'time(s)')
        ax4.xaxis.set_major_locator(mdates.SecondLocator(interval=2))
        ax4.xaxis.set_major_formatter(formatter)       

        
        _, data_l, df_ND_x_r, df_ND_y_r, df_ND_x_l, df_ND_y_l = ND.Nystagmus(data_r, data_l)
        print(3)

        ax1.plot('time', 'x', data = data_r, c = "g", label = 'Eye_R')
        ax1.plot('time', 'avg_x', data = data_r, c = "grey",label = 'avg')
        ax1.plot('time', 'movstd_x', data = data_r, color='b', label='moving_std')
        ax1.plot('time', 'x', data = df_ND_x_r, color='r', label='ND')


        ax2.plot('time', 'y', data = data_r, c = "g", label = 'Eye_R')
        ax2.plot('time', 'avg_y', data = data_r, c = "grey",label = 'avg')
        ax2.plot('time', 'movstd_y', data = data_r, color='b', label='moving_std')
        ax2.plot('time', 'y', data = df_ND_y_r, color='r', label='ND')


        ax3.plot('time', 'x', data = data_l, c = "g", label = 'Eye_L')
        ax3.plot('time', 'avg_x', data = data_l, c = "grey",label = 'avg')
        ax3.plot('time', 'movstd_x', data = data_l, color='b', label='moving_std')
        ax3.plot('time', 'x', data = df_ND_x_l, color='r', label='ND')

        ax4.plot('time', 'y', data = data_l, c = "g", label = 'Eye_L')
        ax4.plot('time', 'avg_y', data = data_l, c = "grey",label = 'avg')
        ax4.plot('time', 'movstd_y', data = data_l, color='b', label='moving_std')
        ax4.plot('time', 'y', data = df_ND_y_l, color='r', label='ND')

        ax1.legend()
        ax2.legend()
        ax3.legend()
        ax4.legend()

        img_path1 = os.path.join(path, f"eyetrace_{res_id}_R_X.png")
        img_path2 = os.path.join(path, f"eyetrace_{res_id}_R_Y.png")
        img_path3 = os.path.join(path, f"eyetrace_{res_id}_L_X.png")
        img_path4 = os.path.join(path, f"eyetrace_{res_id}_L_Y.png")
        print(4)
        fig1.savefig(img_path1)
        fig2.savefig(img_path2)
        fig3.savefig(img_path3)
        fig4.savefig(img_path4)

        for i in range(10):
            if progress_callback:
                progress_callback(60+i)
    
    def bppv_plot(x_max, x_min, y_max, y_min, df, path, label, i, progress_start, progress_end, progress_callback=None):

        img_path = os.path.join(path,f"{i}.png")

        fig = plt.figure()
        fig, ax = plt.subplots(figsize=(6,6),sharex=True)

        ax.set_xlim([x_min, x_max]) 
        ax.set_ylim([y_min, y_max])
        
        ax.set_xlabel(xlabel = 'X_point')
        ax.set_ylabel(ylabel = 'Y_point')

        ax.axis('off') 

        ax.scatter('x', 'y', data = df, c = "blue", label = label, s = 25)

        ax.legend()

        fig.savefig(img_path, bbox_inches='tight', pad_inches=0) 

        if progress_callback:
                progress_percent = progress_start + int((i + 1) / len(df) * (progress_end - progress_start))
                progress_callback(progress_percent)

    def Nystagmus(data_r, data_l):
            a_r, x_r, a1_r, y1_r=[]            
            a_l, x_l, a1_l, y1_l=[]

            #Eye R
            x_avg_r = np.average(data_r['x'])
            y_avg_r = np.average(data_r['y'])

            data_r['avg_x'] = x_avg_r
            data_r['avg_y'] = y_avg_r

            moving_std_x_r = data_r['x'].rolling(window=2).std()
            moving_std_y_r = data_r['y'].rolling(window=2).std()
            moving_average_x_r = moving_std_x_r.mean()
            moving_average_y_r = moving_std_y_r.mean()

            d_x_r = np.max(moving_std_x_r)
            n_x_r= (d_x_r)/(d_x_r-moving_average_x_r)

            d_y_r = np.max(moving_std_y_r)
            n_y_r= (d_y_r)/(d_y_r-moving_average_y_r)

            data_r['movstd_x'] = moving_std_x_r
            data_r['movstd_y'] = moving_std_y_r
            print(data_r)
            ND_x_r =pd.DataFrame(columns = {'x','time'})

            for i in range(len(moving_std_x_r)):
                if n_x_r<data_r['movstd_x'][i] <= d_x_r :     
                    x_r.append(data_r['x'][i])
                    a_r.append(data_r['time'][i])
            ND_x_r['x'] = x_r
            ND_x_r['time'] = a_r

            ND_y_r =pd.DataFrame(columns = {'y','time'})

            for i in range(len(moving_std_y_r)):
                if n_y_r<data_r['movstd_y'][i] <= d_y_r :     
                    y1_r.append(data_r['y'][i])
                    a1_r.append(data_r['time'][i])

            ND_y_r['y'] = y1_r
            ND_y_r['time'] = a1_r

            #Eye L
            x_avg_l = np.average(data_l['x'])
            y_avg_l = np.average(data_l['y'])
            
            data_l['avg_x'] = x_avg_l
            data_l['avg_y'] = y_avg_l

            moving_std_x_l = data_l['x'].rolling(window=2).std()
            moving_std_y_l = data_l['y'].rolling(window=2).std()
            moving_average_x_l = moving_std_x_l.mean()
            moving_average_y_l = moving_std_y_l.mean()
            
            d_x_l = np.max(moving_std_x_l)
            n_x_l= (d_x_l)/((d_x_l)-moving_average_x_l)
            
            d_y_l = np.max(moving_std_y_l)
            n_y_l= (d_y_l)/(d_y_l-moving_average_y_l)

            data_l['movstd_x'] = moving_std_x_l
            data_l['movstd_y'] = moving_std_y_l
            ND_x_l =pd.DataFrame(columns = {'x','time'})

            for i in range(len(moving_std_x_l)):
                if n_x_l<data_l['movstd_x'][i] <= d_x_l :     
                    x_l.append(data_l['x'][i])
                    a_l.append(data_l['time'][i])
            ND_x_l['x'] = x_l
            ND_x_l['time'] = a_l

            ND_y_l =pd.DataFrame(columns = {'y','time'})

            for i in range(len(moving_std_y_l)):
                if n_y_l<data_l['movstd_y'][i] <= d_y_l :     
                    y1_l.append(data_l['y'][i])
                    a1_l.append(data_l['time'][i])

            ND_y_l['y'] = y1_l
            ND_y_l['time'] = a1_l

            df_ND_x_r = pd.merge(ND_x_r,data_r, how='inner')
            df_ND_y_r = pd.merge(ND_y_r,data_r, how='inner')

            df_ND_x_l = pd.merge(ND_x_l,data_l, how='inner')
            df_ND_y_l = pd.merge(ND_y_l,data_l, how='inner')

            print(data_r, data_l, df_ND_x_r, df_ND_y_r, df_ND_x_l, df_ND_y_l)

            return data_r, data_l, df_ND_x_r, df_ND_y_r, df_ND_x_l, df_ND_y_l
    
    def ND_kernel(data_r, data_l,progress_callback = None):

        df_ND_x_r, df_ND_y_r, df_ND_x_l, df_ND_y_l = ND.Nystagmus(data_r, data_l)

        std_avg_x_r = df_ND_x_r['movstd_x'].mean()
        std_avg_y_r = df_ND_y_r['movstd_y'].mean()

        if std_avg_x_r > std_avg_y_r :
            res_r = 'HC-BPPV'
            if std_avg_y_r >= (std_avg_x_r - 1):
                res_r = 'PC-BPPV'
        elif std_avg_x_r < std_avg_y_r :
            if std_avg_x_r >= (std_avg_y_r - 1):
                res_r = 'PC-BPPV'

        std_avg_x_l = df_ND_x_l['movstd_x'].mean()
        std_avg_y_l = df_ND_y_l['movstd_y'].mean()

        if std_avg_x_l > std_avg_y_l :
            res_l = 'HC-BPPV'
            if std_avg_y_l >= (std_avg_x_l - 1):
                res_l = 'PC-BPPV'
        elif std_avg_x_l < std_avg_y_l :
            if std_avg_x_l >= (std_avg_y_l - 1):
                res_l = 'PC-BPPV'


        if res_r == res_l : 
            kernel = res_r
        else:
            kernel = '정밀 판독 필요'

        print(kernel)

        for i in range(10):
            if progress_callback:
                progress_callback(90+i)
        
        return kernel
    

    def System(self, path, date, progress_callback=None):

        V_name = os.path.basename(path)

        with ND.SSH() as tunnel:

            sql_imginfo = f"SELECT videoid FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_info = ND.DB_select(tunnel, sql_imginfo)

            id_info_row = id_info.iloc[0]      
            v_id = str(id_info_row["videoid"]).zfill(4)
            res_id = v_id +"_"+ V_name

            r_o_path, l_o_path, r_res_path, l_res_path, Result_path = ND.folder(res_id)

            fps, total_frames, frame_r_array, frame_l_array, img_r_o, img_l_o = ND.read_and_cut_frames(path, r_o_path, l_o_path, progress_callback)

            pred_r, pred_l = ND.predict_and_preprocess(frame_r_array, frame_l_array)

            sql_insert_pupils = "INSERT INTO Pupils (imageid, x, y, max_distance, min_distance, slope) VALUES (%s, %s, %s, %s, %s, %s);"
            ND.process_ellips(tunnel, sql_insert_pupils, pred_r, v_id, V_name, "R", 40, 50, progress_callback)
            ND.process_ellips(tunnel, sql_insert_pupils, pred_l, v_id, V_name, "L", 50, 60, progress_callback)


            sql_R_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_R_%';"
            sql_L_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_L_%';"
            

            df_R_pupils = ND.DB_select(tunnel, sql_R_pupils)
            df_L_pupils = ND.DB_select(tunnel, sql_L_pupils)
            
            t_list = ND.time_list(fps, total_frames)
            df_R_pupils['time'] = pd.to_datetime(t_list, format='%S.%f', errors='raise')
            df_L_pupils['time'] = pd.to_datetime(t_list, format='%S.%f', errors='raise')   

            # df_R_pupils, df_L_pupils,_,_,_,_ = ND.Nystagmus(df_R_pupils, df_L_pupils)

            # ND.plot_point(df_R_pupils, df_L_pupils,res_id, Result_path, progress_callback)

            new_size = (465,462)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            r_out_res = cv2.VideoWriter(r_res_path, fourcc, fps, new_size)
            l_out_res = cv2.VideoWriter(l_res_path, fourcc, fps, new_size)

            res_img_path = os.path.join(Result_path,'img')
            
            #---------------------------------------
            r_x_max = df_R_pupils["x"].max()
            r_x_min = df_R_pupils["x"].min()
            r_y_max = df_R_pupils["y"].max()
            r_y_min = df_R_pupils["y"].min()

            if not os.path.exists(res_img_path):
                os.makedirs(res_img_path)

            for i in range(len(df_R_pupils)):
                ND.bppv_plot(r_x_max, r_x_min, r_y_max, r_y_min, df_R_pupils[:i+1], res_img_path, "Eye_R", i+1, 70, 80, progress_callback)

            for i in range(len(df_R_pupils)):
                img_path = os.path.join(res_img_path, f"{i+1}.png")
                color_img = cv2.imread(img_path)
                r_out_res.write(color_img)

            r_out_res.release()
            shutil.rmtree(os.path.join(Result_path,"img"))

            #---------------------------------------

            l_x_max = df_L_pupils["x"].max()
            l_x_min = df_L_pupils["x"].min()
            l_y_max = df_L_pupils["y"].max()
            l_y_min = df_L_pupils["y"].min()

            if not os.path.exists(res_img_path):
                os.makedirs(res_img_path)

            for i in range(len(df_L_pupils)):
                ND.bppv_plot(l_x_max, l_x_min, l_y_max, l_y_min, df_L_pupils[:i+1], res_img_path, "Eye_L", i+1, 80, 90, progress_callback)

            for i in range(len(df_L_pupils)):
                img_path = os.path.join(res_img_path, f"{i+1}.png")
                color_img = cv2.imread(img_path)
                l_out_res.write(color_img)

            l_out_res.release()
            shutil.rmtree(os.path.join(Result_path,"img"))

            # kernel = ND.ND_kernel(df_R_pupils, df_L_pupils, progress_callback)

            # sql_kenel = "INSERT INTO kernellesions (videoid, kernellesion) VALUES (%s, %s);"
            # ND.DB_Insert(tunnel, sql_kenel( id_info_row["videoid"], kernel))

            cv2.destroyAllWindows()
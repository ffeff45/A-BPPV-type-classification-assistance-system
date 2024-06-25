import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from sshtunnel import SSHTunnelForwarder
import pymysql
import cv2
import os
import sys
import datetime
np.set_printoptions(threshold=sys.maxsize)
import tensorflow as tf

class Center_point_plot():

    def __init__(self):
        super().__init__()

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
            
 
    def center_point(self, path, date,fps): 
        # path = "C:\\Users\\kreyu\\Desktop\\4grade\\NDT\\ND\\data\\Rt_Apo_BPPV_Short.mp4"
        V_name = os.path.basename(path)
        # fps = AviSlicingImg.get(cv2.CAP_PROP_FPS)
        # date = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        # fps = 24
       

        with Center_point_plot.SSH() as tunnel:
            sql_imgid = f"SELECT videoid,videoname FROM Videos WHERE videoname = '{V_name}' AND videodate = '{date}';"
            id_df = Center_point_plot.DB_select(tunnel, sql_imgid)                    
            row_1 = id_df.iloc[0]      
            v_id = str(row_1["videoid"]).zfill(4)
            res_id = v_id +"_"+ str(row_1["videoname"])
           
          
            sql_R_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_R_%' ;"
            sql_L_pupils = f"SELECT x,y FROM Pupils WHERE imageid LIKE '{v_id}_{V_name}_L_%' ;"
        
            df_R_pupils = Center_point_plot.DB_select(tunnel, sql_R_pupils)
            df_L_pupils = Center_point_plot.DB_select(tunnel, sql_L_pupils)

            t_d= []

            for frame_count in range(len(df_L_pupils)):
                duration = frame_count / fps if fps > 0 else 0  
                td = datetime.timedelta(seconds=duration)
                t_d.append(td)
            
            df_R_pupils['time'] = t_d
            df_L_pupils['time'] = t_d
            
            
            user_p = "C:\\Users\\kreyu\\Desktop\\4grade\\NDT\\ND" #본인 경로로 변경
            folrder_o = "\\"+f"{res_id}"
            folder_result = "\\Result\\"+f"{res_id}"
            
            r_o_path = os.makedirs(user_p+folrder_o+'\\Eye_R')
            l_o_path = os.makedirs(user_p+folrder_o+'\\Eye_L')
            r_res_path = os.makedirs(user_p+folder_result+'\\Eye_R')
            l_res_path = os.makedirs(user_p+folder_result+'\\Eye_L')
            res_eye_trace = os.makedirs(user_p+folder_result+'\\eyetrace')
        

            df_R_pupils.to_csv('./R_point.csv',index=False)
            df_L_pupils.to_csv('./L_point.csv',index=False)
            
          
        Center_point_plot.plot_point(df_R_pupils,df_L_pupils,res_id,res_eye_trace)
        Center_point_plot.bppv_plot(path,df_R_pupils,df_L_pupils,r_o_path,l_o_path,r_res_path,l_res_path)

    def plot_point(data_r, data_l, res_id, res_p) :            
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

        ax1.set_ylim(0,320)
        ax1.set_ylabel(ylabel = 'X_point')
        
        ax2.set_ylim(0,240)
        
        ax2.set_ylabel(ylabel = 'Y_point')
        ax2.set_xlabel(xlabel = 'time(s)')
        
        ax1.plot([data_l].iloc[:,[2]], [data_l].iloc[:,[0]], data = data_l,c = "g" ,label = 'Eye_L')
        ax1.plot([data_r].iloc[:,[2]], [data_r].iloc[:,[0]], data = data_r,c = "r" ,label = 'Eye_R')
        ax2.plot([data_l].iloc[:,[2]], [data_l].iloc[:,[1]], data = data_l,c = "g" ,label = 'Eye_L')
        ax2.plot([data_r].iloc[:,[2]], [data_r].iloc[:,[1]], data = data_r,c = "r" ,label = 'Eye_R')

        ax1.legend()
        ax2.legend()
        fig.savefig(f'"{res_p}"'+'\\'f'"{res_id}"'+'.jpg',dpi = 300)

       

    def bppv_plot(path, data_r, data_l,r_o_p,l_o_p,res_r_path,res_l_path) :
        video = cv2.VideoCapture(path)       
        if not video.isOpened():
            print("Could not open:", path)

        fps = Center_point_plot.get(cv2.CAP_PROP_FPS)
            
        length = len(data_r)
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
        out_r_res = cv2.VideoWriter(res_r_path, fourcc, fps, new_size)
        out_l_res = cv2.VideoWriter(res_l_path, fourcc, fps, new_size)
        
        #elli_list DB에서 알아서 x,y 가져와서 value1, value2에 넣으시오.
        # elli_list 대신 df len 쓰면 될 듯
        
        for i in range(len(data_r)):
            value1 = int(data_r.iloc[:,[0]])
            value2 = int(data_r.iloc[:,[1]])
            cv2.circle(img_u_r,(value1,value2), 2, 255, -1)
            out_r_res.write(img_u_r)

        for i in range(len(data_l)):
            value1 = int(data_l.iloc[:,[0]])
            value2 = int(data_l.iloc[:,[1]])
            cv2.circle(img_u_l,(value1,value2), 2, 255, -1)
            out_l_res.write(img_u_l)
            
        # return out.release()

        
        
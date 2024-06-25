import cv2
import os
import matplotlib.pyplot as plt 
import numpy as np


class AviSlicingImg():

    def __init__(self):
        super().__init__()
        
        self.img_rt_np_array = []
        self.img_lt_np_array = []

    def img_slice_save(self, path):
        
        video = cv2.VideoCapture(path) #'' 사이에 사용할 비디오 파일의 경로 및 이름을 넣어주도록 함
        print("1")
        length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_r_array = []
        frame_l_array = []
        
        if not video.isOpened():
            print("Could not Open :", path)
            exit(0)
            
        for i in range(length):
            ret, frame = video.read()        
            
            if ret:
                frame_rt = frame[:, :161]
                frame_r = cv2.resize(frame_rt, (320, 240))
                
                frame_lt = frame[:, 161:]
                frame_l = cv2.resize(frame_lt, (320, 240))
                
                frame_r_array.append(frame_r)
                frame_l_array.append(frame_l)
                
            else:
                print("NOpe")
                
        self.img_rt_np_array = np.array(frame_r_array)
        self.img_lt_np_array = np.array(frame_l_array)
        
        np.save("frame_rt",self.img_rt_np_array)
        np.save("frame_lt",self.img_lt_np_array) #DB 넘어가는 코드 작성되면 사라져용 확인용
        
        video.release()
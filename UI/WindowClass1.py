import os
import sys
import cv2
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
import datetime
from PyQt5 import uic  # ui 파일을 사용하기 위한 모듈
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from WindowClass2 import WindowClass2
from media import CMultiMedia

# UI파일 연결 코드
UI_class = uic.loadUiType("SC1.ui")[0]


class WindowClass1(QMainWindow, UI_class):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(620, 860)
        self.move(250, 100)
    


        # 파일 관련 버튼
        self.Sc1_Result.clicked.connect(self.showSecondWindow)
        self.Sc1_Add.clicked.connect(self.pushAddClicked)
        self.Sc1_Del.clicked.connect(self.pushDeldClicked)
        self.Sc1_Save.clicked.connect(self.saveToDatabase)

        # 재생 관련 버튼
        self.Sc1_Play.clicked.connect(self.clickPlay)
        self.Sc1_Stop.clicked.connect(self.clickStop)
        self.Sc1_Pause.clicked.connect(self.clickPause)
        self.Sc1_Next.clicked.connect(self.clickNext)
        self.Sc1_Prev.clicked.connect(self.clickPrev)
    
        self.Sc1_ListView.itemDoubleClicked.connect(self.dbClickList)
        self.Sc1_VideoSpeed.sliderMoved.connect(self.barChanged) 
        
        #동영상
        self.mp = CMultiMedia(self, self.Sc1_Video)
        pal = QPalette()        
        pal.setColor(QPalette.Background, Qt.black)
        self.Sc1_Video.setAutoFillBackground(True)
        self.Sc1_Video.setPalette(pal)


        # QTableWidget 초기화
        self.Sc1_ListView.setColumnCount(5)
        self.Sc1_ListView.setHorizontalHeaderLabels(['FileName', 'Length', 'FPS','Size',"Date"])
        self.Sc1_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Sc1_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.duration = ''

        self.Sc1_ListView.currentCellChanged.connect(self.currentcellchanged_event)

    # 선택한 셀이 바뀌면 발생하는 이벤트
    def currentcellchanged_event(self, row, col, pre_row, pre_col):
        current_data = self.Sc1_ListView.item(row, col) # 현재 선택 셀 값
        pre_data = self.Sc1_ListView.item(pre_row, pre_col) # 이전 선택 셀 값
        if pre_data is not None:
            print("이전 선택 셀 값 : ", pre_data.text())
        else:
            print("이전 선택 셀 값 : 없음")

        print("현재 선택 셀 값 : ", current_data.text())



    # 페이지 바꾸는 코드
    def showSecondWindow(self):
        self.clickPause()
        self.second_window = WindowClass2()
        self.second_window.exec()
        self.show()
    

    # 파일 추가 버튼
    def pushAddClicked(self):
        self.fname = QFileDialog.getOpenFileName(self, '파일선택', '', 'All Files(*.*)')

        # 파일이 선택된 경우
        if self.fname[0]:  
            filename = os.path.basename(self.fname[0])

            cap = cv2.VideoCapture(self.fname[0])

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 영상 길이 계산
            duration = frame_count / fps if fps > 0 else 0  
            duration = int(duration * 1000)
            td = datetime.timedelta(milliseconds=duration)
            stime = str(td)
            idx = stime.rfind('.')
            duration = stime[:idx]

            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            size = f'{int(width)}x{int(height)}'

            date = (datetime.date.today().isoformat())

            # 리스트에 새로운 항목 추가
            self.Sc1_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            row = self.Sc1_ListView.rowCount()
            self.Sc1_ListView.setRowCount(row)
            self.Sc1_ListView.insertRow(row)
            self.Sc1_ListView.setItem(row, 0, QTableWidgetItem(filename))
            self.Sc1_ListView.setItem(row, 1, QTableWidgetItem(duration))
            self.Sc1_ListView.setItem(row, 2, QTableWidgetItem(f'{fps:.2f}'))
            self.Sc1_ListView.setItem(row, 3, QTableWidgetItem(size))
            self.Sc1_ListView.setItem(row, 4, QTableWidgetItem(date))
            
            # 동영상 리스트에 동영상 추가
            self.mp.addMedia(self.fname[0])

    # 파일 삭제 버튼
    def pushDeldClicked(self):
        text = ' '
        self.video_name.setText(text)        
        row = self.Sc1_ListView.currentRow()
        self.Sc1_ListView.removeRow(row)
        self.mp.delMedia(row)

    # 동영상 재생 버튼 수정필요
    def clickPlay(self):
        current_index = self.Sc1_ListView.currentRow()
        if current_index == -1:  # 선택된 항목이 없는 경우
            current_index = 0  # 기본적으로 첫 번째 항목을 선택
        text = self.Sc1_ListView.item(current_index, 0).text()
        self.video_name.setText(text)
        self.mp.playMedia(current_index)

    # 동영상 정지 버튼
    def clickStop(self):
        text = ' '
        self.video_name.setText(text)
        self.mp.stopMedia()

    # 동영상 일시정지 버튼
    def clickPause(self):
        self.mp.pauseMedia()

    def clickPrev(self):
        current_index = self.Sc1_ListView.currentRow()
        if current_index > 0:
            current_index -= 1
        else:
            current_index = self.Sc1_ListView.rowCount() - 1  # 첫 번째 항목인 경우 마지막 항목으로 돌아가기

        self.Sc1_ListView.setCurrentCell(current_index, 0)  # 현재 셀을 업데이트
        text = self.Sc1_ListView.item(current_index, 0).text()
        self.video_name.setText(text)
        self.mp.playMedia(current_index)


    def clickNext(self):
        current_index = self.Sc1_ListView.currentRow()
        if current_index < self.Sc1_ListView.rowCount() - 1:
            current_index += 1
        else:
            current_index = 0  # 마지막 항목인 경우 처음 항목으로 돌아가기

        self.Sc1_ListView.setCurrentCell(current_index, 0)  # 현재 셀을 업데이트
        text = self.Sc1_ListView.item(current_index, 0).text()
        self.video_name.setText(text)
        self.mp.playMedia(current_index)


    # 두 번 선택 시 동영상 바꾸는 버튼

    def dbClickList(self, item):
        row_1 = self.Sc1_ListView.row(item)
        text = self.Sc1_ListView.item(row_1, 0).text()
        self.video_name.setText(text)
        self.mp.playMedia(row_1)
    
    # 재생 바 
    def barChanged(self, pos):   
        self.mp.posMoveMedia(pos)

    # 재생 상태 
    def updateState(self, msg):
        self.Sc1_StatusText.setText(msg)
    
    # 바 상태 업데이트
    def updateBar(self, duration):
        self.Sc1_VideoSpeed.setRange(0,duration)    
        self.Sc1_VideoSpeed.setSingleStep(int(duration/10))
        self.Sc1_VideoSpeed.setPageStep(int(duration/10))
        self.Sc1_VideoSpeed.setTickInterval(int(duration/10))
        td = datetime.timedelta(milliseconds=duration)        
        stime = str(td)
        idx = stime.rfind('.')
        self.duration = stime[:idx]

    # 재생 시간
    def updatePos(self, pos):
        self.Sc1_VideoSpeed.setValue(pos)
        td = datetime.timedelta(milliseconds=pos)
        stime = str(td)
        idx = stime.rfind('.')
        now_duration = stime[:idx]
        stime = f'{now_duration} / {self.duration}'
        self.Sc1_TimeText.setText(stime)

    #저장버튼
    def saveToDatabase(self):
        date1 = datetime.datetime.strptime(length, '%H:%M:%S').time()
        size01  = size.split('x')
        

        for row in range(self.Sc1_ListView.rowCount()):
            filename_item = self.Sc1_ListView.item(row, 0).text()
            length_item = self.Sc1_ListView.item(row, 1).text()
            fps_item = self.Sc1_ListView.item(row, 2).text()
            height_item = self.Sc1_ListView.item(row, 3).text()
            weight_item = self.Sc1_ListView.item(row, 4).text()
            size_item = self.Sc1_ListView.item(row, 5).text()
            date_item = self.Sc1_ListView.item(row, 6).text()

        
            filename = filename_item.text()
            length = int(length_item.text())
            fps = float(fps_item.text())
            height,weight = int(size01[0],size01[1])


            print(type(length))
            print(type(fps))
            print(type(height1))
            print(type(weight1))
            print(type(size01))
            print(type(date1))
            





        # ssh_host = '210.126.67.40'
        # ssh_port = 7785
        # ssh_username = 'qhdrmfdl1234'
        # ssh_password = 'Wndlf7785!'

        # sql_hostname = '127.0.0.1'
        # sql_username = 'bppv'
        # sql_password = '1234'
        # sql_database = 'BppvNDdb'

        # tunnel = SSHTunnelForwarder((ssh_host, ssh_port),
        #                         ssh_username=ssh_username,
        #                         ssh_password=ssh_password,
        #                         remote_bind_address=('127.0.0.1', 3306))
        
        # with tunnel:
        #     print("== SSH Tunnel ==")
        #     conn = pymysql.connect(
        #             host=sql_hostname, 
        #             user=sql_username,
        #             password=sql_password, 
        #             charset="utf8",
        #             db=sql_database,
        #             port=tunnel.local_bind_port)
            
        #     cursor = conn.cursor(pymysql.cursors.DictCursor)
        #     sql = "INSERT INTO Videos (videoid, videoleght, videofps, videosize, videodate) VALUE ( %s, %s, %s,%s, %s);"
        #     cursor.execute(sql)

        #     for row in range(self.Sc1_ListView.rowCount()):
        #                 filename = self.Sc1_ListView.item(row, 0).text()
        #                 length = self.Sc1_ListView.item(row, 1).text()
        #                 fps = self.Sc1_ListView.item(row, 2).text()
        #                 size = self.Sc1_ListView.item(row, 3).text()
        #                 date = self.Sc1_ListView.item(row, 4).text()
        #                 result = cursor.fetchall()

            
        #     conn.commit()
        #     conn.close()
        
        self.Sc1_ListView.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()

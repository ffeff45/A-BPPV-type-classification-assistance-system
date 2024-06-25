import os
import sys
import cv2
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
import datetime
from PyQt5 import *
from PyQt5 import uic 
from PyQt5.QtWidgets import *
from PyQt5.QtCore import * #Qt, QBasicTimer
from PyQt5.QtGui import * #QPalette
from WindowClass2 import WindowClass2
from media import CMultiMedia
from AviSlicingImg import AviSlicingImg
from PyQt5.QtCore import QThread, pyqtSignal

# UI파일 연결 코드
UI_class = uic.loadUiType("SC1.ui")[0]
UI_Loading = uic.loadUiType("loading.ui")[0]

class DatabaseThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, list_view_items, parent=None):
        super(DatabaseThread, self).__init__(parent)
        self.list_view_items = list_view_items

    def run(self):
        try:
            ssh_host = '210.126.67.40'
            ssh_port = 7785
            ssh_username = 'qhdrmfdl1234'
            ssh_password = 'Wndlf7785!'

            sql_hostname = '127.0.0.1'
            sql_username = 'bppv'
            sql_password = '1234'
            sql_database = 'BppvDB'

            tunnel = SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                remote_bind_address=('127.0.0.1', 3306)
            )

            with tunnel:
                # print("== SSH 터널 연결 ==")
                conn = pymysql.connect(
                    host=sql_hostname,
                    user=sql_username,
                    password=sql_password,
                    charset="utf8",
                    db=sql_database,
                    port=tunnel.local_bind_port
                )

                cursor = conn.cursor(pymysql.cursors.DictCursor)
                sql = "INSERT INTO Videos (videoname, videolenght, videofps, videowidth, videoheight, videodate, videosize) VALUES (%s, %s, %s, %s, %s, %s, %s);"

                for item in self.list_view_items:
                    filename = item['filename']
                    length = item['length']
                    fps = item['fps']
                    size = item['size']
                    date = item['date']
                    frame = item['frame']

                    length_time = datetime.datetime.strptime(length, '%H:%M:%S').time()
                    fps = float(fps)
                    width, height = map(int, size.split('x'))
                    frame = float(frame)

                    # print(filename, length, fps, width, height, date, frame)
                    cursor.execute(sql, (filename, length, fps, width, height, date, frame))

                conn.commit()
                conn.close()

                for item in self.list_view_items:
                    path = item['path']
                    AviSlicingImg.img_slice_save(self, path, date)

        except Exception as e:
            self.error.emit(str(e))

        self.finished.emit()



class loading(QWidget,UI_Loading):
    
    def __init__(self,parent):
        super(loading,self).__init__(parent) 
        self.setupUi(self) 
        self.widget_center()
        self.show()

        # 동적 이미지 추가
        self.movie = QMovie('loading.gif', QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)
        # QLabel에 동적 이미지 삽입
        self.label.setMovie(self.movie)
        self.movie.start()
        # 윈도우 해더 숨기기
        self.setWindowFlags(Qt.FramelessWindowHint)
    
    # 위젯 정중앙 위치
    def widget_center(self):
        self.move(40,70)



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
        
        # 클릭 관련 버튼
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
        self.Sc1_ListView.setColumnCount(7)
        self.Sc1_ListView.setHorizontalHeaderLabels(['FileName', 'Length', 'FPS','Size',"Date", "Frame","Path"])
        self.Sc1_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Sc1_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.duration = ''
        self.Sc1_ListView.currentCellChanged.connect(self.currentcellchanged_event)


    # 선택한 셀이 바뀌면 발생하는 이벤트
    def currentcellchanged_event(self, row, col, pre_row, pre_col):
        current_data = self.Sc1_ListView.item(row, col)  # 현재 선택 셀 값
        pre_data = self.Sc1_ListView.item(pre_row, pre_col)  # 이전 선택 셀 값
        if pre_data is not None:
            print("이전 선택 셀 값 : ", pre_data.text())
        else:
            print("이전 선택 셀 값 : 없음")

        if current_data is not None:
            print("현재 선택 셀 값 : ", current_data.text())
        else:
            print("현재 선택 셀 값 : 없음")


    def showSecondWindow(self):
        self.clickPause()
        self.second_window = WindowClass2()
        self.setDisabled(True)  # 원래 창 비활성화
        self.second_window.exec_()
        self.show()
        self.setDisabled(False)  #원래 창 활성화


    # 파일 추가 버튼
    def pushAddClicked(self):
        self.fname = QFileDialog.getOpenFileName(self, '파일선택', '', 'All Files(*.*)')

        # 파일이 선택된 경우
        if self.fname[0]:  
            filename = os.path.basename(self.fname[0])

            cap = cv2.VideoCapture(self.fname[0])

            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            # 영상 길이 계산
            duration = frame_count / fps if fps > 0 else 0  
            td = datetime.timedelta(seconds=duration)
            stime = str(td)
            idx = stime.rfind('.')
            duration = stime[:idx]

            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            size = f'{int(width)}x{int(height)}'


            date = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            print(date)
            frame_count = str(frame_count)

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
            self.Sc1_ListView.setItem(row, 5, QTableWidgetItem(frame_count))
            self.Sc1_ListView.setItem(row, 6, QTableWidgetItem(self.fname[0]))
            
            # 동영상 리스트에 동영상 추가
            self.mp.addMedia(self.fname[0])


    def pushDeldClicked(self):
        current_row = self.Sc1_ListView.currentRow()
        if current_row >= 0:  # 선택된 항목이 있는 경우
            self.Sc1_ListView.removeRow(current_row)
            self.mp.delMedia(current_row)


        # 동영상 재생 버튼 
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
        self.Sc1_TimeText.setText('')
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

    def saveToDatabase(self):
        # 로딩 위젯 생성 및 표시
        self.loading = loading(self)
        self.loading.show()
        QApplication.processEvents()  # 로딩 위젯이 표시되도록 이벤트 처리

        # QTableWidget의 모든 항목 가져오기
        list_view_items = []
        for row in range(self.Sc1_ListView.rowCount()):
            item = {
                'filename': self.Sc1_ListView.item(row, 0).text(),
                'length': self.Sc1_ListView.item(row, 1).text(),
                'fps': self.Sc1_ListView.item(row, 2).text(),
                'size': self.Sc1_ListView.item(row, 3).text(),
                'date': self.Sc1_ListView.item(row, 4).text(),
                'frame': self.Sc1_ListView.item(row, 5).text(),
                'path': self.Sc1_ListView.item(row, 6).text()
            }
            list_view_items.append(item)

        # 백그라운드 작업 스레드 시작
        self.thread = DatabaseThread(list_view_items)
        self.thread.finished.connect(self.onDatabaseSaveFinished)
        self.thread.error.connect(self.onDatabaseSaveError)
        self.thread.start()

    def onDatabaseSaveFinished(self):
        self.loading.deleteLater()
        msg = QMessageBox()
        msg.move(470, 400)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("알림")
        msg.setText("저장 완료")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        self.Sc1_ListView.setRowCount(0)
        myWindow1.show()

    def onDatabaseSaveError(self, error_message):
        self.loading.deleteLater()
        msg = QMessageBox()
        msg.move(470, 400)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("에러")
        msg.setText("DB 저장 중 에러 발생:\n" + error_message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()
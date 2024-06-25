import os
import sys
import cv2
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

        self.Sc1_Result.clicked.connect(self.showSecondWindow)
        self.Sc1_Add.clicked.connect(self.pushAddClicked)
        self.Sc1_Play.clicked.connect(self.clickPlay)
        self.Sc1_Stop.clicked.connect(self.clickStop)
        self.Sc1_Pause.clicked.connect(self.clickPause)

        self.Sc1_ListView.itemDoubleClicked.connect(self.dbClickList)

        #동영상
        self.mp = CMultiMedia(self, self.Sc1_Video)

        pal = QPalette()        
        pal.setColor(QPalette.Background, Qt.black)
        self.Sc1_Video.setAutoFillBackground(True)
        self.Sc1_Video.setPalette(pal)


        # QTableWidget 초기화
        self.Sc1_ListView.setColumnCount(3)
        self.Sc1_ListView.setHorizontalHeaderLabels(['파일명', '프레임 수', '길이'])


    def showSecondWindow(self):   # 페이지 바꾸는 코드
        self.hide()
        self.second_window = WindowClass2()
        self.second_window.exec()
        self.show()
    

    # 파일선택버튼
    def pushAddClicked(self):
        self.fname = QFileDialog.getOpenFileName(self, '파일선택', '', 'All Files(*.*)')
        if self.fname[0]:  # 파일이 선택된 경우
            filename = os.path.basename(self.fname[0])
            cap = cv2.VideoCapture(self.fname[0])
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0  # 영상 길이 계산

            # 리스트에 새로운 항목 추가
            row = self.Sc1_ListView.rowCount()
            self.Sc1_ListView.setRowCount(row)
            self.Sc1_ListView.insertRow(row)
            self.Sc1_ListView.setItem(row, 0, QTableWidgetItem(filename))
            self.Sc1_ListView.setItem(row, 1, QTableWidgetItem(str(frame_count)))
            self.Sc1_ListView.setItem(row, 2, QTableWidgetItem(f"{duration:.2f} 초"))
            self.Sc1_ListView.resizeColumnsToContents()

            #동영상 
            self.mp.addMedia(self.fname[0])
    
    def updateState(self, msg):
        self.Sc1_StatusText.setText(msg)

    def clickPlay(self):
        index = self.Sc1_ListView.rowCount() -1     
        self.mp.playMedia(index)
    
    def clickStop(self):
        self.mp.stopMedia()

    def clickPause(self):
        self.mp.pauseMedia()
    
    def dbClickList(self, item):
        row_1 = self.Sc1_ListView.row(item)
        self.mp.playMedia(row_1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()

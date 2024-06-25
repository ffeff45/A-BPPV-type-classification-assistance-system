import os
import sys
import cv2
from PyQt5 import uic  # ui 파일을 사용하기 위한 모듈
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from WindowClass2 import WindowClass2

# UI파일 연결 코드
UI_class = uic.loadUiType("SC1.ui")[0]
class WindowClass1(QMainWindow, UI_class):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(620, 860)

        self.Sc1_Result.clicked.connect(self.showSecondWindow)
        self.Sc1_Add.clicked.connect(self.pushAddClicked)

        #동영상


        # QTableWidget 초기화
        self.Sc1_ListView.setColumnCount(3)
        self.Sc1_ListView.setHorizontalHeaderLabels(['파일명', '프레임 수', '길이'])

        # add버튼
        self.add_count = 0

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
            self.Sc1_ListView.setRowCount(self.add_count)
            row_position = 0
            self.Sc1_ListView.insertRow(row_position)
            self.Sc1_ListView.setItem(row_position, 0, QTableWidgetItem(filename))
            self.Sc1_ListView.setItem(row_position, 1, QTableWidgetItem(str(frame_count)))
            self.Sc1_ListView.setItem(row_position, 2, QTableWidgetItem(f"{duration:.2f} 초"))
            self.Sc1_ListView.resizeColumnsToContents()
            self.add_count +=1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()

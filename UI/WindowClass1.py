import sys
import cv2
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic   # ui 파일을 사용하기 위한 모듈 import
from WindowClass2 import WindowClass2

#UI파일 연결 코드
UI_class = uic.loadUiType("SC1.ui")[0]
class WindowClass1(QMainWindow, UI_class):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(620, 860)

        self.Sc1_Result.clicked.connect(self.showSecondWindow)
        self.Sc1_Add.clicked.connect(self.pushAddClicked)

    def showSecondWindow(self):
        # 두 번째 윈도우를 생성하고 보여줍니다.
        self.hide()
        self.second_window = WindowClass2()
        self.second_window.exec()
        self.show()  # 현재 윈도우를 숨깁니다.

#파일선택버튼


    def pushAddClicked(self):
        self.fname = QFileDialog.getOpenFileName(self, '파일선택','','All Files(*.*)')
        filename = os.path.basename(self.fname[0])
        cap = cv2.VideoCapture(self.fname[0])
        filesize = float(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(filesize)
        self.Sc1_ListView.setItem(0, 0, QTableWidgetItem(filename))
        self.Sc1_ListView.setItem(0, 1, QTableWidgetItem(str(filesize)))
        self.Sc1_ListView.resizeColumnsToContents()










if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow1 = WindowClass1()
    myWindow1.show()
    app.exec_()

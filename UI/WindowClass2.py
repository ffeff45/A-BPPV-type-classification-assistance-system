import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *

#UI파일 연결 코드
UI_class = uic.loadUiType("SC2.ui")[0]

class WindowClass2(QDialog,QWidget, UI_class):
    def __init__(self):
        super(WindowClass2, self).__init__()
        self.setupUi(self)
        self.setFixedSize(620,860)
        self.show()

        # 홈 버튼에 클릭 이벤트 핸들러를 추가합니다.
        self.Sc2_Home.clicked.connect(self.goToFirstWindow)

    def goToFirstWindow(self):
        self.close()  # 현재 윈도우를 닫습니다.

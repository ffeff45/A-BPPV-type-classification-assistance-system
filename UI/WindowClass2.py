import sys
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QMovie

# from media import CMultiMedia

#UI파일 연결 코드
UI_class = uic.loadUiType("SC2.ui")[0]

class WindowClass2(QDialog,QWidget, UI_class):
    def __init__(self):
        super(WindowClass2, self).__init__()
        self.setupUi(self)
        self.setFixedSize(620,860)
        self.move(900, 100)
        self.show()


        # 홈 버튼에 클릭 이벤트 핸들러를 추가
        self.Sc2_Home.clicked.connect(self.goToFirstWindow)

        path1 = "C:/Users/hyejin/KakaoTalk_20240531_032447766.gif"
        # self.play_mp4()
        self.play_gif(path1)

        # self.Sc2_ListView.setColumnCount(4)
        # self.Sc2_ListView.setHorizontalHeaderLabels(['FileName', 'Date', 'Canal','Percent'])
        # self.Sc2_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.Sc2_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        
        # self.canal = "Superior canal"
        # self.percent = "92%"

        # self.Sc2_ResultView.setPlainText(" ")
        # self.Sc2_ResultView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # self.Sc2_ResultView.append(self.canal)
        # self.Sc2_ResultView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        # self.Sc2_ResultView.append(" ")

        # self.Sc2_ResultView.append(self.percent)
        # self.Sc2_ResultView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        
        # self.tabelView()



    # def play_mp4(self):
    #     mp4_path = ""
    #     media_content = QMediaContent(QUrl.fromLocalFile(mp4_path))
    #     self.Sc2_Video.setMedia(media_content)
    #     self.Sc2_Video.play()

    def play_gif(self, path):
        movie = QMovie(path)
        self.Sc2_Video.setMovie(movie)
        movie.start()


        # filename = "Class4_100022"
        # date = "2024-05-22"


        # qPixmapVar = QPixmap()
        # qPixmapVar.load("duck.jpg")
        # self.Sc2_Img.setPixmap(qPixmapVar.scaled(285,380))

        # self.tabelView()

    def goToFirstWindow(self):
        self.close()  # 현재 윈도우를 닫습니다.
        
    
    # def tabelView(self):
    #     ssh_host = '210.126.67.40'
    #     ssh_port = 7785
    #     ssh_username = 'qhdrmfdl1234'
    #     ssh_password = 'Wndlf7785!'

    #     sql_hostname = '127.0.0.1'
    #     sql_username = 'bppv'
    #     sql_password = '1234'
    #     sql_database = 'BppvDB'

    #     tunnel = SSHTunnelForwarder((ssh_host, ssh_port),
    #                             ssh_username=ssh_username, 
    #                             ssh_password=ssh_password,
    #                             remote_bind_address = ('127.0.0.1', 3306))
        
    #     with tunnel:
    #         print("== SSH Tunnel ==")
    #         conn = pymysql.connect(
    #                 host=sql_hostname, 
    #                 user=sql_username,
    #                 password=sql_password, 
    #                 charset="utf8",
    #                 db=sql_database,
    #                 port=tunnel.local_bind_port)
            
    #         cursor = conn.cursor(pymysql.cursors.DictCursor)
    #         sql = "SELECT * FROM BppvDB.Videos;"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #         conn.close()

    #     df = pd.DataFrame(result)
    #     df.head()

    #     for i in range(2):
    #         row_1 = df.iloc[i]
    #         filename = row_1["videoname"]
    #         date =str(row_1["videofps"])
    #         row = self.Sc2_ListView.rowCount()
    #         # self.Sc1_ListView.setRowCount(row)
    #         self.Sc2_ListView.insertRow(row)
    #         self.Sc2_ListView.setItem(row, 0, QTableWidgetItem(filename))
    #         self.Sc2_ListView.setItem(row, 1, QTableWidgetItem(date))
    #         self.Sc2_ListView.setItem(row, 2, QTableWidgetItem(self.canal))
    #         self.Sc2_ListView.setItem(row, 3, QTableWidgetItem(self.percent))


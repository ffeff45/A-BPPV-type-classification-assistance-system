import sys
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap
import resource2_rc

# UI파일 연결 코드
UI_class = uic.loadUiType("SC2_re.ui")[0]

class WindowClass2(QDialog, QWidget, UI_class):
    def __init__(self):
        super(WindowClass2, self).__init__()
        self.setupUi(self)
        # self.setFixedSize(1000, 1040)
        self.move(450, 100)

        qPixmapVar = QPixmap()
        qPixmapVar.load("C:/Users/hyejin/ND/Result/0005_안진안진안진/eyetrace_0005_안진안진안진.mp4.png")
        self.Sc2_img.setPixmap(qPixmapVar)


        # 홈 버튼에 클릭 이벤트 핸들러를 추가
        self.Sc2_Home.clicked.connect(self.goToFirstWindow)
        self.Sc2_ListView.setColumnCount(3)
        self.Sc2_ListView.setHorizontalHeaderLabels(['FileName', 'Date', 'Canal'])
        self.Sc2_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Sc2_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 여러 개의 QMediaPlayer 객체 생성
        self.mediaPlayer1 = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer2 = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer3 = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer4 = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # 각 비디오 플레이어를 출력할 QVideoWidget 설정
        self.mediaPlayer1.setVideoOutput(self.Sc2_VideoL)
        self.mediaPlayer2.setVideoOutput(self.Sc2_VideoR)
        self.mediaPlayer3.setVideoOutput(self.Sc2_DotL)
        self.mediaPlayer4.setVideoOutput(self.Sc2_DotR)

        # Play 버튼 클릭 이벤트 핸들러 설정
        # self.Sc2_Play.clicked.connect(self.play_videos)

        self.show()

        self.tabelView()

    def showEvent(self, event):
        super().showEvent(event)
        self.play_videos()


    def play_videos(self):
        self.play_mp4(self.mediaPlayer1, "C:/Users/hyejin/ND/Original/0005_안진안진안진/Eye_L.mp4")
        self.play_mp4(self.mediaPlayer2, "C:/Users/hyejin/ND/Result/0005_안진안진안진/Eye_L.mp4")
        self.play_mp4(self.mediaPlayer3, "C:/Users/hyejin/ND/Original/0005_안진안진안진/Eye_R.mp4")
        self.play_mp4(self.mediaPlayer4, "C:/Users/hyejin/ND/Result/0005_안진안진안진/Eye_R.mp4")

    def play_mp4(self, player, path):
        player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        player.play()
        player.mediaStatusChanged.connect(lambda status: self.handle_media_status(player, path, status))

    def handle_media_status(self, player, path, status):
        if status == QMediaPlayer.EndOfMedia:
            player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            player.play()

    def goToFirstWindow(self):
        self.close()  # 현재 윈도우를 닫습니다.
    
    def tabelView(self):
        ssh_host = '210.126.67.40'
        ssh_port = 7785
        ssh_username = 'qhdrmfdl1234'
        ssh_password = 'Wndlf7785!'

        sql_hostname = '127.0.0.1'
        sql_username = 'bppv'
        sql_password = '1234'
        sql_database = 'BppvDB'

        tunnel = SSHTunnelForwarder((ssh_host, ssh_port),
                                    ssh_username=ssh_username,
                                    ssh_password=ssh_password,
                                    remote_bind_address=('127.0.0.1', 3306))
        
        with tunnel:
            print("== SSH Tunnel ==")
            conn = pymysql.connect(
                    host=sql_hostname, 
                    user=sql_username,
                    password=sql_password, 
                    charset="utf8",
                    db=sql_database,
                    port=tunnel.local_bind_port)
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT Videos.videoname, Videos.videodate, kernellesions.kernellesion FROM Videos JOIN kernellesions ON Videos.videoid = kernellesions.videoid;"
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()

        df = pd.DataFrame(result)
        print(df.head())

        for i in range(len(df)):
            row_1 = df.iloc[i]
            filename = row_1["videoname"]
            date = str(row_1["videodate"])
            canal = str(row_1["kernellesion"])
            print(filename)
            row = self.Sc2_ListView.rowCount()
            self.Sc2_ListView.setRowCount(row + 1)
            self.Sc2_ListView.setItem(row, 0, QTableWidgetItem(filename))
            self.Sc2_ListView.setItem(row, 1, QTableWidgetItem(date))
            self.Sc2_ListView.setItem(row, 2, QTableWidgetItem(canal))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowClass2()
    sys.exit(app.exec_())
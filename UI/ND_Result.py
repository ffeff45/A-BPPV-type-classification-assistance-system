import sys
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt, QThread, pyqtSignal
import resource2_rc

# UI파일 연결 코드
UI_class = uic.loadUiType("ND_Result.ui")[0]

class DatabaseThread(QThread):
    data_loaded = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)

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
                conn = pymysql.connect(
                    host=sql_hostname,
                    user=sql_username,
                    password=sql_password,
                    charset="utf8",
                    db=sql_database,
                    port=tunnel.local_bind_port
                )

                cursor = conn.cursor(pymysql.cursors.DictCursor)
                sql = "SELECT Videos.videoname, Videos.videodate, kernellesions.kernellesion FROM Videos JOIN kernellesions ON Videos.videoid = kernellesions.videoid;"
                cursor.execute(sql)
                result = cursor.fetchall()
                conn.close()

            df = pd.DataFrame(result)
            self.data_loaded.emit(df)
        except Exception as e:
            self.error_occurred.emit(str(e))


class WindowResult(QDialog, QWidget, UI_class):
    def __init__(self):
        super(WindowResult, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("ND")
        self.setWindowIcon(QIcon("ND.png"))
        self.move(300, 30)

        self.Sc2_Play.clicked.connect(self.clickPlay)
        self.Sc2_Pause.clicked.connect(self.clickPause)
        self.Sc2_ListView.itemDoubleClicked.connect(self.listDoubleClicked)

        qPixmapVar1 = QPixmap()
        qPixmapVar1.load("C:/Users/hyejin/ND/Result/graR.png")
        self.Sc2_imgRx.setPixmap(qPixmapVar1)

        qPixmapVar2 = QPixmap()
        qPixmapVar2.load("C:/Users/hyejin/ND/Result/graL.png")
        self.Sc2_imgLx.setPixmap(qPixmapVar2)

        self.Sc2_Home.clicked.connect(self.goToFirstWindow)
        self.Sc2_ListView.setColumnCount(3)
        self.Sc2_ListView.setHorizontalHeaderLabels(['FileName', 'Date', 'Canal'])
        self.Sc2_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Sc2_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.mediaPlayers = [
            QMediaPlayer(None, QMediaPlayer.VideoSurface),
            QMediaPlayer(None, QMediaPlayer.VideoSurface),
            QMediaPlayer(None, QMediaPlayer.VideoSurface),
            QMediaPlayer(None, QMediaPlayer.VideoSurface)
        ]

        self.mediaPlayers[0].setVideoOutput(self.Sc2_VideoR)
        self.mediaPlayers[1].setVideoOutput(self.Sc2_VideoL)
        self.mediaPlayers[2].setVideoOutput(self.Sc2_DotR)
        self.mediaPlayers[3].setVideoOutput(self.Sc2_DotL)

        self.show()

        self.database_thread = DatabaseThread()
        self.database_thread.data_loaded.connect(self.populate_table)
        self.database_thread.error_occurred.connect(self.handle_database_error)
        self.database_thread.start()

        self.video_paths = [
            "C:/Users/hyejin/ND/Original/0005_안진안진안진/Eye_R.mp4",
            "C:/Users/hyejin/ND/Original/0005_안진안진안진/Eye_L.mp4",
            "C:/Users/hyejin/ND/Result/R_video.mp4",
            "C:/Users/hyejin/ND/Result/L_video.mp4"
        ]

    def goToFirstWindow(self):
        self.close()

    def clickPlay(self):
        for player in self.mediaPlayers:
            player.play()

    def clickPause(self):
        for player in self.mediaPlayers:
            player.pause()

    def playMedia(self, index):
        for i, player in enumerate(self.mediaPlayers):
            player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_paths[i])))
            player.play()

    def listDoubleClicked(self):
        current_index = self.Sc2_ListView.currentRow()
        self.playMedia(current_index)

    def pushDeldClicked(self):
        current_row = self.Sc2_ListView.currentRow()
        if current_row >= 0:  # 선택된 항목이 있는 경우
            self.Sc2_ListView.removeRow(current_row)
            # 이 부분에서 적절한 미디어 삭제 로직을 추가해야 합니다.

    def populate_table(self, df):
        for i in range(len(df)):
            row_1 = df.iloc[i]
            filename = row_1["videoname"]
            date = str(row_1["videodate"])
            canal = str(row_1["kernellesion"])
            row = self.Sc2_ListView.rowCount()
            self.Sc2_ListView.setRowCount(row + 1)
            self.Sc2_ListView.setItem(row, 0, QTableWidgetItem(filename))
            self.Sc2_ListView.setItem(row, 1, QTableWidgetItem(date))
            self.Sc2_ListView.setItem(row, 2, QTableWidgetItem(canal))

    def handle_database_error(self, error_message):
        QMessageBox.critical(self, "Database Error", error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowResult()
    sys.exit(app.exec_())

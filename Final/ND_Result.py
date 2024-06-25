import sys
import os
import getpass
import pymysql
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt, QThread, pyqtSignal
import resource2_rc
from ND_Algorithm import ND

# UI파일 연결 코드
UI_class = uic.loadUiType("ND_Result.ui")[0]

class DatabaseThread(QThread):
    data_loaded = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DatabaseThread, self).__init__(parent)

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
                sql = "SELECT Videos.videoid, Videos.videoname, Videos.videodate, kernellesions.kernellesion FROM Videos JOIN kernellesions ON Videos.videoid = kernellesions.videoid;"
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

        self.Sc2_Home.clicked.connect(self.goToFirstWindow)
        self.Sc2_ListView.setColumnCount(3)
        self.Sc2_ListView.setHorizontalHeaderLabels(['FileName', 'Date','bppvlesion'])
        self.Sc2_ListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.Sc2_ListView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.imagelabels = [
            self.Sc2_imgRx,
            self.Sc2_imgRy,
            self.Sc2_imgLx,
            self.Sc2_imgLy,
        ]

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

    def folder(self, filename):        
        filename = filename[:-4]

        username = getpass.getuser()
        user_path = os.path.join("C:\\Users", username)

        ND_path = os.path.join(user_path, 'ND')

        Original_path = os.path.join(ND_path, 'Original', filename)
        Result_path = os.path.join(ND_path, 'Result', filename)

        r_o_path = os.path.join(Original_path, 'Eye_R.mp4')
        l_o_path = os.path.join(Original_path, 'Eye_L.mp4')
        r_res_path = os.path.join(Result_path, 'Eye_R.mp4')
        l_res_path = os.path.join(Result_path, 'Eye_L.mp4')

        r_x_path = os.path.join(Result_path, f"{filename}.mp4_R_X.png")
        r_y_path = os.path.join(Result_path, f"{filename}.mp4_R_Y.png")
        l_x_path = os.path.join(Result_path, f"{filename}.mp4_L_X.png")
        l_y_path = os.path.join(Result_path, f"{filename}.mp4_L_Y.png")

        if not os.path.exists(ND_path):
            os.makedirs(ND_path)

        if not os.path.exists(Original_path):
            os.makedirs(Original_path)
        
        if not os.path.exists(Result_path):
            os.makedirs(Result_path)

        print(r_x_path,r_y_path, l_x_path,l_y_path)

        return r_o_path, l_o_path, r_res_path, l_res_path, Result_path, r_x_path,r_y_path, l_x_path,l_y_path

    def goToFirstWindow(self):
        self.close()

    def clickPlay(self):
        current_index = self.Sc2_ListView.currentRow()
        if current_index == -1:  # 선택된 항목이 없는 경우
            current_index = 0  # 기본적으로 첫 번째 항목을 선택
        self.playMediaAndDisplayImages(current_index)

    def clickPause(self):
        for player in self.mediaPlayers:
            player.pause()

    def playMediaAndDisplayImages(self, index):
        filename = self.Sc2_ListView.item(index, 0).text()
        canal = self.Sc2_ListView.item(index, 2).text()       

        self.Sc2_ResultView.setText(f"{canal}로 의심됩니다.")
        
        r_o_path, l_o_path, r_res_path, l_res_path, _, r_x_path,r_y_path, l_x_path,l_y_path = self.folder(filename)
        video_paths = [r_o_path, l_o_path, r_res_path, l_res_path]
        
        qPixmapVar1 = QPixmap()
        qPixmapVar2 = QPixmap()
        qPixmapVar3 = QPixmap()
        qPixmapVar4 = QPixmap()

        qPixmapVar1.load(r_x_path)
        qPixmapVar2.load(r_y_path)
        qPixmapVar3.load(l_x_path)
        qPixmapVar4.load(l_y_path)

        self.Sc2_imgRx.setPixmap(qPixmapVar1)
        self.Sc2_imgRy.setPixmap(qPixmapVar2)
        self.Sc2_imgLx.setPixmap(qPixmapVar3)
        self.Sc2_imgLy.setPixmap(qPixmapVar4)

        for i, player in enumerate(self.mediaPlayers):
            player.setMedia(QMediaContent(QUrl.fromLocalFile(video_paths[i])))
            player.play()

    def listDoubleClicked(self):
        current_index = self.Sc2_ListView.currentRow()
        self.playMediaAndDisplayImages(current_index)

    def populate_table(self, df):
        for i in range(len(df)):
            row_1 = df.iloc[i]
            videoid = row_1["videoid"]
            v_id = str(videoid).zfill(4)
            filename = f'{v_id}_{row_1["videoname"]}'
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

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QMovie

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.resize(400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.label = QLabel("Video Player", alignment = Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.btn_play_mp4 = QPushButton("Play MP4")
        self.btn_play_mp4.clicked.connect(self.play_mp4)
        self.layout.addWidget(self.btn_play_mp4)

        self.btn_play_gif = QPushButton("Play GIF")
        self.btn_play_gif.clicked.connect(self.play_gif)
        self.layout.addWidget(self.btn_play_gif)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.movie_player = QLabel()
        self.layout.addWidget(self.movie_player)

    def play_mp4(self):
        mp4_path = ""
        media_content = QMediaContent(QUrl.fromLocalFile(mp4_path))
        self.media_player.setMedia(media_content)
        self.media_player.play()

    def play_gif(self):
        gif_path = "C:/Users/hyejin/KakaoTalk_20240531_032447766.gif"
        movie = QMovie(gif_path)
        self.movie_player.setMovie(movie)
        movie.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())

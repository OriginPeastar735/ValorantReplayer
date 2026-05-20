import tensor
import sys, cv2, os
import pygetwindow as gw
from colorama import Fore, Back, Style

#GUI系のインポート
from PyQt6.QtWidgets import(QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QSlider, QSplitter)
from PyQt6.QtGui import QIcon, QPixmap

#動画系のインポート
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt

killtime = []#ninsiki()から送られるタイムの格納
deathtime = []

class Window(QWidget):
    def __init__(self):#__init__()は自動呼び出しされる関数
        super().__init__()
        self.setWindowTitle("VALORANT Replayer")
        self.setGeometry(0,0,1530,780)
        self.init_ui()

    def init_ui(self):
        #ウィンドウの設定
        
        os.environ['TF_CPP_IN_LOG_LEVEL'] = '2'

        #メインレイアウトの作成
        mainLayout = QVBoxLayout()#QVは縦にレイアウト
        self.setLayout(mainLayout)

        #ウィジェットを分割
        splitter = QSplitter(Qt.Orientation.Vertical)#縦のスプリッタ―

        #上側に動画表示領域の作成
        self.videoWidget = QVideoWidget()
        splitter.addWidget(self.videoWidget)

        #コントロール部分(ボタンとスライダー)
        controlWidget = QWidget()
        controlLayout = QVBoxLayout(controlWidget)

        #再生バーの上にスペースを作成
        spacer = QLabel("")
        spacer.setFixedHeight(1)
        controlLayout.addWidget(spacer)

        #再生バーの作成
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.slider.setRange(0, 1000000)#マイクロ秒単位に設定
        self.slider.sliderPressed.connect(self.slider_pressed)
        self.slider.sliderReleased.connect(self.slider_released)
        controlLayout.addWidget(self.slider)

        #再生停止ボタン
        self.playButton = QPushButton("Play/Pause Video")
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play_video)
        saisei = QSplitter(Qt.Orientation.Horizontal,self)
        controlLayout.addWidget(saisei)
        self.skip5s = QPushButton("Skip 5s")
        self.skip5s.setEnabled(False)
        self.skip5s.clicked.connect(self.skip_5s)
        self.back5s = QPushButton("Backward 5s")
        self.back5s.setEnabled(False)
        self.back5s.clicked.connect(self.back_5s)
        saisei.addWidget(self.back5s)
        saisei.addWidget(self.playButton)
        saisei.addWidget(self.skip5s)

        #動画選択ボタン
        self.openButton = QPushButton("Import your file")
        self.openButton.setIcon(QIcon("magaoneko.jpg"))
        self.openButton.clicked.connect(self.open_video)
        controlLayout.addWidget(self.openButton)

        #コントロールウィジェットをレイアウトに追加
        splitter.addWidget(controlWidget)

        #QSpllitterをレイアウトに追加
        mainLayout.addWidget(splitter)

        #QMediaPlayerのセットアップ
        self.mediaPlayer = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.setAudioOutput(self.audioOutput)

        # シグナル接続
        self.mediaPlayer.positionChanged.connect(self.update_slider)
        self.mediaPlayer.durationChanged.connect(self.update_slider_range)


    def open_video(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Video Files (*.mp4 *.avi)"
        )
        if filePath:
            #QUrlに変換
            fileUrl = QUrl.fromLocalFile(filePath)
            self.mediaPlayer.setSource(fileUrl)#動画ファイルをセット
            print(f"file loaded: {filePath}")
            cap = cv2.VideoCapture(filePath)
            sumFrame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            videoLength = sumFrame // fps #秒数で渡す
            print(f"videoLength = {int(videoLength/60)}m{videoLength%60}s ")
            #イベント検出を開始
            self.ninsiki(filePath, videoLength)
            self.playButton.setEnabled(True)#再生ボタンを有効化
            self.back5s.setEnabled(True)
            self.skip5s.setEnabled(True)
            self.slider.setEnabled(True)
    
    def play_video(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()#再生中なら一時停止
        else:
            self.mediaPlayer.play()#再生

    def back_5s(self):
        current_position = self.mediaPlayer.position()#現在の位置を取得 関数の戻り値にそのまま加算とかは無理
        self.mediaPlayer.setPosition(current_position - 5000)

    def skip_5s(self):
        current_position = self.mediaPlayer.position()
        self.mediaPlayer.setPosition(current_position + 5000)


    def update_slider(self, position):
        #再生位置をスライダーに反映
        print(f"position changed: {position}")
        if not self.slider.isSliderDown():
            self.slider.setValue(position)
        
    def update_slider_range(self, duration):
        print(f"duration changed: {duration}")
        #動画の長さに基づいてスライダーの範囲を更新
        self.slider.setRange(0, duration)

    def slider_pressed(self):
        self.mediaPlayer.pause()

    def slider_released(self):
        position = self.slider.value()
        self.mediaPlayer.setPosition(position)
        self.mediaPlayer.play()

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()

        print(f"mouse clicked at: x = {x}, y = {y}")

    def ninsiki(self, videoPath, videoLength):

        inputFilename = videoPath

        target_time = 0

        killFlag = False
        deathFlag = False

        top = 760
        bottom = 1080
        left = 800
        right = 1120

        index = 0

        while index <= videoLength:
            #kerasモデルで画像認識
            print(f"index = {index}")
            target_time = index * 1000 #ミリ秒単位
            resultindex = tensor.trimVideo(inputFilename, target_time, top, bottom, left, right) # 返り値を格納、毎週初期化
            if resultindex == 1:# 0:nothing, 1:killed, 2:death
                if not killFlag:
                    print(Fore.BLUE + "killed" + Style.RESET_ALL)
                    killtime.append(int((1485 / videoLength) * (index)) + 12)
                    #self.killmark(index, width, len(arrayimg), height)
                    for i in range(len(killtime)):
                        if len(killtime) == 0:
                            break
                        print(f"killpin{i}.x = {killtime[i]}")
                        if killtime[i] > 1530:
                            print("warning: killpin.x is over the width")
                        #self.add_killpin(killtime[i])
                        killpin = QLabel(self)
                        pixmap = QPixmap(r"C:\Users\daiki\AppData\Local\Programs\Python\Python311\valore\killpin.png")
                        pixmap = pixmap.scaled(18,30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        killpin.move(killtime[i], 640)
                        killpin.setPixmap(pixmap)
                        killpin.show()
                    killFlag = True
                    index += 1
                else:
                    killFlag = False
                    index += 1
            elif resultindex == 2:
                if not deathFlag:
                    deathFlag = True
                    index += 1
                else:
                    print(Fore.RED + "YOU DIED" + Style.RESET_ALL)
                    print("skip to buy phase.")
                    deathtime.append(int((1485 / videoLength) * (index-1)) + 12)
                    for i in range(len(deathtime)):
                        if len(deathtime) == 0:
                            break
                        print(f"deathpin{i}.x = {deathtime[i]}")
                        if deathtime[i] > 1530:
                            print("warning: deathpin.x is over the width")
                        #self.add_killpin(killtime[i])
                        deathpin = QLabel(self)
                        dpixmap = QPixmap(r"C:\Users\daiki\AppData\Local\Programs\Python\Python311\valore\deathpin.png")
                        dpixmap = dpixmap.scaled(18,30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        deathpin.move(deathtime[i], 640)
                        deathpin.setPixmap(dpixmap)
                        deathpin.show()
                        deathFlag = False
                        index += 30 #画像認識を50秒スキップ
                    if index > videoLength:
                        break
            else:
                if killFlag:
                    killFlag = False
                    index += 1
                else:
                    index += 1

if __name__ == "__main__":

    qap = QApplication(sys.argv)
    waku = Window()
    waku.show()
    qap.exec()
import os
import sys

import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QMessageBox

from TrackProgram import TrackProgram
from MicStream import MicStream
import traceback

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join('speech-rtc-c9ccd2b3139f.json')

class Controller(QWidget):
    app = QApplication(sys.argv)
    track: TrackProgram
    mic1_stream: MicStream
    mic2_stream: MicStream
    # Array of data
    #display_list = []
    mode = '양방향'
    display_mode = ['양방향', '단방향']
    audio_info_list = []
    lang_list = ['한국어', '영어', '중국어', '일본어', '독일어', '프랑스어', '스페인어', '포르투갈어', '이탈리아어', '러시아어', '베트남어']
    fontSize_list = [18, 24, 48, 96]
    # UI Object
    startButton: QPushButton
    stopButton: QPushButton
    refreshButton: QPushButton
    cb_display: QComboBox
    cb_mic1: QComboBox
    cb_mic2: QComboBox
    cb_lang1: QComboBox
    cb_lang2: QComboBox
    cb_fontSize: QComboBox
    # Setting Attribute
    lang1 = '한국어'
    lang2 = '영어'
    mic1: object
    mic2: object
    font_size = 48

    def __init__(self):
        super().__init__()
        self.initUI()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Exit', quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                if self.track.is_alive():
                    QMessageBox.question(self, 'Error', '프로그램이 완전히 종료되지 않았습니다.', QMessageBox.Ok, QMessageBox.Ok)
                    event.ignore()
                else:
                    event.accept()
            except:
                event.accept()
        else:
            event.ignore()

    def initUI(self):
        self.startButton = QPushButton("시작", self)
        self.stopButton = QPushButton("종료", self)
        self.stopButton.setEnabled(False)
        self.refreshButton = QPushButton("새로고침", self)
        self.cb_display = QComboBox(self)
        self.cb_display.addItems(self.display_mode)
        self.cb_mic1 = QComboBox(self)
        self.cb_mic2 = QComboBox(self)
        self.cb_lang1 = QComboBox(self)
        self.cb_lang2 = QComboBox(self)
        self.cb_fontSize = QComboBox(self)

        self.refresh()

        grid = QGridLayout()
        grid.addWidget(QLabel("디스플레이"), 0, 0)
        grid.addWidget(QLabel("마이크1"), 1, 0)
        grid.addWidget(QLabel("마이크2"), 2, 0)
        grid.addWidget(QLabel("언어1"), 3, 0)
        grid.addWidget(QLabel("언어2"), 4, 0)
        grid.addWidget(QLabel("폰트 크기"), 5, 0)

        self.cb_display.activated[str].connect(self.select_display_mode)
        grid.addWidget(self.cb_display, 0, 1)
        self.cb_mic1.activated[str].connect(self.select_mic1)
        grid.addWidget(self.cb_mic1, 1, 1)
        self.cb_mic2.activated[str].connect(self.select_mic2)
        grid.addWidget(self.cb_mic2, 2, 1)
        self.cb_lang1.activated[str].connect(self.select_lang1)
        self.cb_lang1.setCurrentIndex(0)
        grid.addWidget(self.cb_lang1, 3, 1)
        self.cb_lang2.activated[str].connect(self.select_lang2)
        self.cb_lang2.setCurrentIndex(1)
        grid.addWidget(self.cb_lang2, 4, 1)
        self.cb_fontSize.activated[str].connect(self.select_fontSize)
        self.cb_fontSize.setCurrentIndex(2)
        grid.addWidget(self.cb_fontSize, 5, 1)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        self.startButton.clicked.connect(self.start)
        hbox.addWidget(self.startButton)
        self.stopButton.clicked.connect(self.stop)
        hbox.addWidget(self.stopButton)
        self.refreshButton.clicked.connect(self.refresh)
        hbox.addWidget(self.refreshButton)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(grid)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.setLayout(vbox)

        self.setWindowTitle("Track Controller")
        self.center()
        self.resize(480, 360)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

    def refresh(self):
        # initialize ComboBox
        # self.cb_display.clear()
        self.cb_mic1.clear()
        self.cb_mic2.clear()
        self.cb_lang1.clear()
        self.cb_lang2.clear()
        self.cb_fontSize.clear()
        # mic setting
        audio = pyaudio.PyAudio()
        host_info = audio.get_default_host_api_info()
        for index in range(host_info.get("deviceCount")):
            desc = audio.get_device_info_by_host_api_device_index(host_info.get("index"), index)
            if desc.get('maxInputChannels') != 0:
                self.audio_info_list.append(desc)
                self.cb_mic1.addItem(desc['name'])
                self.cb_mic2.addItem(desc['name'])
                print('감지된 마이크 : ' + desc['name'])
        self.mic1 = self.audio_info_list[0]
        self.mic2 = self.audio_info_list[0]
        # display setting
        # display_number = self.app.desktop().screenCount()
        # print("감지된 모니터 수 : ", display_number)
        # display_index = 0
        # for i in range(0, display_number):
        #     display_index = display_index + i
        #     self.display_list.append(display_index)
        #     self.cb_display.addItem(str(display_index))
        # language setting
        self.cb_lang1.addItems(self.lang_list)
        self.cb_lang2.addItems(self.lang_list)
        # font-Size setting
        self.cb_fontSize.addItems(str(font_size) for font_size in self.fontSize_list)
        self.cb_lang1.setCurrentIndex(0)
        self.cb_lang2.setCurrentIndex(1)

    def start(self):
        if self.lang1 == self.lang2:
            # 동일한 언어 선택 시
            QMessageBox.question(self, 'Error', '동일한 언어로 설정되었습니다.', QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.startButton.setEnabled(False)
            self.stopButton.setEnabled(True)
            try:
                self.track = TrackProgram((self.lang1, self.lang2), int(self.font_size), self.mode)
                self.track.start()
                self.mic1_stream = MicStream('mic1', self.track, (self.lang1, self.lang2), mic=self.mic1, flags='Left')
                self.mic2_stream = MicStream('mic2', self.track, (self.lang2, self.lang1), mic=self.mic2, flags='Right')
                self.mic1_stream.start()
                self.mic2_stream.start()
            except Exception as e:
                print("Start Error:", e)
                print(traceback.format_exception())

    def stop(self):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.track.stop()
        self.mic1_stream.stop()
        self.mic2_stream.stop()

    def end(self):
        try:
            if self.track.is_alive():
                self.track.stop()
        except AttributeError:
            print("정상 종료")
        
    def select_display_mode(self, mode):
        if mode == '단방향':
            self.mode = '단방향'
        else:
            self.mode = '양방향'

    def select_mic1(self, mic_name):
        self.mic1 = next((obj for obj in self.audio_info_list if obj['name'] == mic_name), None)

    def select_mic2(self, mic_name):
        self.mic2 = next((obj for obj in self.audio_info_list if obj['name'] == mic_name), None)

    def select_lang1(self, text):
        self.lang1 = text

    def select_lang2(self, text):
        self.lang2 = text

    def select_fontSize(self, font_size):
        self.font_size = font_size


if __name__ == '__main__':
    ex = Controller()
    sys.exit(ex.app.exec())

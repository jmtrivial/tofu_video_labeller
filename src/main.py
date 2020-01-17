from PyQt5.QtCore import QDir, Qt, QUrl, pyqtSlot, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget,
        QTableWidget, QTableWidgetItem, QMainWindow, QAction,
        QAbstractScrollArea, QShortcut)

from utils import create_action
from label_creator import LabelCreatorWidget
from label_editor import LabelEditorWidget
from label_slider import LabelSliderWidget
from signals import SignalBus

import sys
import csv
from functools import partial


class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("Tofu Video Labeller")
        self.setWindowIcon(QIcon('src/static/img/tofu.png'))
        self.comm = SignalBus.instance()
        self.comm.newLabelSignal.connect(self.bindLabelEvent)
        self.initUI()

    def initUI(self):
        videoWidget = self.create_player()
        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                QSizePolicy.Maximum)
        self.create_menu_bar()
        wid = QWidget(self)
        self.setCentralWidget(wid)
        self.set_layout(videoWidget, wid)
        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def create_player(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()
        self.editorWidget = LabelEditorWidget()
        self.creatorWidget = LabelCreatorWidget()
        self.create_control()

        self.playButton.clicked.connect(self.play)
        self.goBackButton.clicked.connect(self.slow)
        self.slowDownButton.clicked.connect(self.speed)
        self.speedUpButton.clicked.connect(self.advance)
        self.advanceButton.clicked.connect(self.back)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        return videoWidget

    def create_control(self):
        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        # TODO: begin
        self.advanceButton = QPushButton()
        self.speedUpButton = QPushButton()
        self.goBackButton = QPushButton()
        self.slowDownButton = QPushButton()
        self.advanceButton.setEnabled(False)
        self.speedUpButton.setEnabled(False)
        self.goBackButton.setEnabled(False)
        self.slowDownButton.setEnabled(False)
        self.labelSlider = LabelSliderWidget()
        # TODO: end

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)

    def create_menu_bar(self):
        openAction = create_action('open.png', '&Open', 'Ctrl+O', 'Open video',
                self.openFile, self)
        csvAction = create_action('save.png', '&Export', 'Ctrl+S',
                'Export to csv', self.exportCsv, self)
        exitAction = create_action('exit.png', '&Exit', 'Ctrl+Q', 'Exit',
                self.exitCall, self)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(csvAction)
        fileMenu.addAction(exitAction)

    def set_layout(self, videoWidget, wid):
        labellingLayout = QVBoxLayout()
        labellingLayout.addWidget(self.creatorWidget)
        labellingLayout.addWidget(self.editorWidget)

        controlLayout = self.make_control_layout()

        videoAreaLayout = QVBoxLayout()
        videoAreaLayout.addWidget(videoWidget)
        videoAreaLayout.addLayout(controlLayout)
        videoAreaLayout.addWidget(self.errorLabel)

        layout = QHBoxLayout()
        layout.addLayout(videoAreaLayout, 4)
        layout.addLayout(labellingLayout)

        wid.setLayout(layout)

    def make_control_layout(self):
        buttonsLayout = QHBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        # TODO: time
        buttonsLayout.addWidget(self.slowDownButton)
        buttonsLayout.addWidget(self.goBackButton)
        buttonsLayout.addWidget(self.playButton)
        buttonsLayout.addWidget(self.advanceButton)
        buttonsLayout.addWidget(self.speedUpButton)
        # TODO: speed
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.positionSlider)
        layout.addWidget(self.labelSlider)
        layout.addLayout(buttonsLayout)
        return layout

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open video",
                QDir.homePath())

        if fileName != '':
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)

    def exitCall(self):
        sys.exit(app.exec_())

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def slow(self):
        pass

    def speed(self):
        pass

    def advance(self):
        pass

    def back(self):
        pass

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def bindLabelEvent(self, keySeq, label):
        bind = QAction(label, self)
        bind.setShortcut(keySeq)
        bind.triggered.connect(partial(self.createMark, label))
        self.addAction(bind)

    def exportCsv(self):
        fileUrl, _ = QFileDialog.getSaveFileUrl(self, QDir.homePath())
        fileName = fileUrl.toLocalFile()

        if fileName != '':
            with open(fileName, mode='w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
                marks = self.editorWidget.get_marks()
                writer.writerows(marks)

    @pyqtSlot()
    def createMark(self, label):
        state = self.mediaPlayer.state()
        if state == QMediaPlayer.PlayingState or state == \
                QMediaPlayer.PausedState:
            self.editorWidget.new_mark(self.mediaPlayer.position()/1000, label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(940, 480)
    player.show()
    sys.exit(app.exec_())



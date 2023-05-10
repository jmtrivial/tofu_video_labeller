from PyQt5.QtCore import QDir, Qt, QUrl, pyqtSlot, pyqtSignal, QCoreApplication, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget,
        QTableWidget, QTableWidgetItem, QMainWindow, QAction,
        QAbstractScrollArea, QShortcut)

from utils import create_action, format_time
from label_creator import LabelCreatorWidget
from label_editor import LabelEditorWidget
from label_slider import LabelSliderWidget
from signals import SignalBus

import sys
import os
import csv
from functools import partial

try:
    from PyQt5.QtWinExtras import QtWin
    myappid = 'tofu_video_labeller.myprod.subprod.version_0.0.1'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class QDoubleClickButton(QPushButton):
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clicked.emit)
        super().clicked.connect(self.checkDoubleClick)

    @pyqtSlot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start(250)

class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("tofu")
        self.setWindowIcon(QIcon(os.path.join('static', 'img', 'tofu.ico')))
        self.comm = SignalBus.instance()
        self.comm.newLabelSignal.connect(self.bindLabelEvent)
        self.comm.delLabelSignal.connect(self.unbindLabelEvent)
        self.rate = 1
        self.initUI()
        self.set_default_shortcuts()
        self.shortcuts = {}

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
        self.mediaPlayer.setNotifyInterval(100)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def create_player(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()
        self.creatorWidget = LabelCreatorWidget()
        self.editorWidget = LabelEditorWidget(self, self.creatorWidget.groups)
        self.create_control()

        self.playButton.clicked.connect(self.play)
        self.speedUpButton.clicked.connect(self.speed)
        self.slowDownButton.clicked.connect(self.slow)
        self.adv3Button.clicked.connect(partial(self.advance, 300))
        self.adv1Button.clicked.connect(partial(self.advance, 100))
        self.goBack3Button.clicked.connect(partial(self.back, 300))
        self.goBack1Button.clicked.connect(partial(self.back, 100))
        self.advanceButton.clicked.connect(partial(self.advance, 5000))
        self.goBackButton.clicked.connect(partial(self.back, 5000))
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.timeBox.doubleClicked.connect(self.onDoubleClickTimeBox)

        return videoWidget

    def set_default_shortcuts(self):
        self.playButton.setShortcut(QKeySequence(Qt.Key_Space))
        self.speedUpButton.setShortcut(QKeySequence(Qt.Key_Up))
        self.slowDownButton.setShortcut(QKeySequence(Qt.Key_Down))
        self.adv1Button.setShortcut(QKeySequence(Qt.Key_Right))
        self.goBack1Button.setShortcut(QKeySequence(Qt.Key_Left))

    def create_control(self):
        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.speedUpButton = QPushButton()
        self.speedUpButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.speedUpButton.setEnabled(False)

        self.slowDownButton = QPushButton()
        self.slowDownButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.slowDownButton.setEnabled(False)

        self.adv1Button = QPushButton()
        self.adv1Button.setToolTip("> 0.1 second")
        self.adv1Button.setIcon(
                self.style().standardIcon(QStyle.SP_ArrowRight))
        self.adv1Button.setEnabled(False)

        self.adv3Button = QPushButton()
        self.adv3Button.setToolTip("> 0.3 second")
        self.adv3Button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.adv3Button.setEnabled(False)

        self.advanceButton = QPushButton()
        self.advanceButton.setToolTip("> 5 seconds")
        self.advanceButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.advanceButton.setEnabled(False)

        self.goBack1Button = QPushButton()
        self.goBack1Button.setToolTip("< 0.1 second")
        self.goBack1Button.setIcon(
                self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.goBack1Button.setEnabled(False)

        self.goBack3Button = QPushButton()
        self.goBack3Button.setToolTip("< 0.3 second")
        self.goBack3Button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.goBack3Button.setEnabled(False)

        self.goBackButton = QPushButton()
        self.goBackButton.setToolTip("< 5 seconds")
        self.goBackButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.goBackButton.setEnabled(False)

        self.timeBox = QDoubleClickButton(format_time(0), self)
        self.timeBox.setToolTip("A double clic on the label set the begin or end timestamp selected in the table")
        self.timeBox.setEnabled(False)

        self.rateBox = QLabel(str(self.rate)+'x', self)
        self.rateBox.setAlignment(Qt.AlignCenter)

        self.labelSlider = LabelSliderWidget(self)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)

    def onDoubleClickTimeBox(self):
        position = self.mediaPlayer.position()
        self.editorWidget.updateSelectedTimestamp(position)
        self.editorWidget.highight_intersecting_items(position)


    def create_menu_bar(self):
        openAction = create_action('open.png', '&Open', 'Ctrl+O', 'Open video',
                self.openFile, self)
        csvExportAction = create_action('save.png', '&Export', 'Ctrl+S',
                'Export to csv', self.exportCsv, self)
        csvImportAction = create_action('open.png', '&Import', 'Ctrl+I',
                'Import from csv', self.importCsv, self)
        exitAction = create_action('exit.png', '&Exit', 'Ctrl+Q', 'Exit',
                self.exitCall, self)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(csvExportAction)
        fileMenu.addAction(csvImportAction)
        fileMenu.addAction(exitAction)

    def set_layout(self, videoWidget, wid):
        labellingLayout = QVBoxLayout()

        spWidget = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        spWidget.setHorizontalStretch(1)
        self.creatorWidget.setSizePolicy(spWidget)
        self.editorWidget.setSizePolicy(spWidget)


        labellingLayout.addWidget(self.creatorWidget, 1)
        labellingLayout.addWidget(self.editorWidget, 1)

        controlLayout = self.make_control_layout()

        videoAreaLayout = QVBoxLayout()
        videoAreaLayout.addWidget(videoWidget, 5)
        videoAreaLayout.addLayout(controlLayout, 1)
        videoAreaLayout.addWidget(self.errorLabel)

        layout = QHBoxLayout()
        layout.addLayout(videoAreaLayout, 3)
        layout.addLayout(labellingLayout, 1)

        wid.setLayout(layout)

    def make_control_layout(self):
        buttonsLayout = QHBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)

        buttonsPlayerLayout = QHBoxLayout()
        buttonsPlayerLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.addLayout(buttonsPlayerLayout, 5)

        buttonsPlayerLayout.addWidget(self.timeBox)
        buttonsPlayerLayout.addWidget(self.goBackButton)
        buttonsPlayerLayout.addWidget(self.goBack3Button)
        buttonsPlayerLayout.addWidget(self.goBack1Button)
        buttonsPlayerLayout.addWidget(self.playButton)
        buttonsPlayerLayout.addWidget(self.adv1Button)
        buttonsPlayerLayout.addWidget(self.adv3Button)
        buttonsPlayerLayout.addWidget(self.advanceButton)
        
        buttonsRateLayout = QHBoxLayout()
        buttonsRateLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.addLayout(buttonsRateLayout, 1)

        buttonsRateLayout.addWidget(self.slowDownButton)
        buttonsRateLayout.addWidget(self.rateBox)
        buttonsRateLayout.addWidget(self.speedUpButton)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.positionSlider)
        layout.addLayout(buttonsLayout)
        layout.addWidget(self.labelSlider)
        return layout


    def setActiveLabel(self, row, begin, end):
        self.activeRow = row
        self.labelSlider.setActiveLabel(begin, end)

    def unsetActiveLabel(self):
        self.labelSlider.unsetActiveLabel()

    def labelSliderStartChanged(self, value):
        self.setPosition(value)
        self.editorWidget.setStartMark(self.activeRow, value)

    def labelSliderEndChanged(self, value):
        self.setPosition(value)
        self.editorWidget.setEndMark(self.activeRow, value)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open video",
                QDir.homePath())

        if fileName != '':
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.absOpenedFile = os.path.abspath(fileName)
            self.openedFile = os.path.basename(fileName)
            self.setWindowTitle("tofu - " + self.openedFile)
            self.playButton.setEnabled(True)
            self.speedUpButton.setEnabled(True)
            self.slowDownButton.setEnabled(True)
            self.advanceButton.setEnabled(True)
            self.adv3Button.setEnabled(True)
            self.adv1Button.setEnabled(True)
            self.goBackButton.setEnabled(True)
            self.goBack3Button.setEnabled(True)
            self.goBack1Button.setEnabled(True)
            self.timeBox.setEnabled(True)
            self.rate = 1

    def exitCall(self):
        QCoreApplication.quit()

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def slow(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.rate -= 0.5
            # TODO: Workaround pt 1
            # https://forum.qt.io/topic/88490/change-playback-rate-at-...
            # ...runtime-problem-with-position-qmediaplayer/8
            currentPos = self.mediaPlayer.position()
            # TODO: Workaround pt 1
            self.mediaPlayer.setPlaybackRate(self.rate)
            # TODO: Workaround pt 2
            self.mediaPlayer.setPosition(currentPos)
            # TODO: Workaround pt 2: end
            self.rateBox.setText(str(self.rate)+'x')

    def speed(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.rate += 0.5
            # TODO: Workaround pt 1
            # https://forum.qt.io/topic/88490/change-playback-rate-at-...
            # ...runtime-problem-with-position-qmediaplayer/8
            currentPos = self.mediaPlayer.position()
            # TODO: Workaround pt 1
            self.mediaPlayer.setPlaybackRate(self.rate)
            # TODO: Workaround pt 2
            self.mediaPlayer.setPosition(currentPos)
            # TODO: Workaround pt 2: end
            self.rateBox.setText(str(self.rate)+'x')

    def advance(self, t=10000):
        currentPos = self.mediaPlayer.position()
        nextPos  = currentPos + t
        self.setPosition(nextPos)

    def back(self, t=10000):
        currentPos = self.mediaPlayer.position()
        nextPos  = max(currentPos - t, 0)
        self.setPosition(nextPos)

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        self.timeBox.setText(format_time(position))
        self.editorWidget.highight_intersecting_items(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
        self.labelSlider.setTotalRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.speedUpButton.setEnabled(False)
        self.slowDownButton.setEnabled(False)
        self.advanceButton.setEnabled(False)
        self.goBackButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def bindLabelEvent(self, keySeq, label):
        bind = QAction(label, self)
        bind.setShortcut(keySeq)
        bind.triggered.connect(partial(self.createMark, label))
        self.shortcuts[keySeq.toString()] = bind
        self.addAction(bind)

    def unbindLabelEvent(self, keySeqStr):
        self.removeAction(self.shortcuts[keySeqStr])
        del self.shortcuts[keySeqStr]

    def getCSVPath(self):
        return os.path.splitext(self.absOpenedFile)[0] + '.csv'

    def importCsv(self):
        if hasattr(self, "openedFile"):
            suggestedName = QUrl.fromLocalFile(self.getCSVPath())
        else:
            suggestedName = QUrl.fromLocalFile(QDir.homePath())

        fileUrl, _ = QFileDialog.getOpenFileUrl(self, "Import marks", suggestedName, "CSV (*.csv)")
        fileName = fileUrl.toLocalFile()

        if fileName != '':
             with open(fileName, mode='r') as csv_file:
                labels = csv.reader(csv_file, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
                self.editorWidget.set_marks(labels)

    def exportCsv(self):
        if hasattr(self, "openedFile"):
            suggestedName = QUrl.fromLocalFile(self.getCSVPath())
        else:
            suggestedName = QUrl.fromLocalFile(QDir.homePath())
    
        fileUrl, _ = QFileDialog.getSaveFileUrl(self, "Export marks", QUrl(suggestedName), "CSV (*.csv)")
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
            self.editorWidget.new_mark(self.mediaPlayer.position(), label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setWindowIcon(QIcon('tofu.ico'))
    player = VideoWindow()
    player.resize(940, 480)
    player.show()
    sys.exit(app.exec_())



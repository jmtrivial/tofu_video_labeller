from PyQt5.QtWidgets import (QLabel, QDialog, QFormLayout, QGroupBox,
                             QPushButton, QSizePolicy, QStyle,
                             QVBoxLayout, QWidget, QLineEdit,
                             QTableWidget, QTableWidgetItem, QAction,
                             QAbstractScrollArea, QFrame, QDialogButtonBox)
from PyQt5.QtCore import pyqtSlot, Qt, QEvent
from PyQt5.QtGui import QIcon, QColor

from utils import format_time, str_to_ms


class LabelEditorWidget(QWidget):

    def __init__(self, control):
        super(LabelEditorWidget, self).__init__()
        self.title = 'Label Editor'
        self.control = control
        self.default_color = None
        self.initUI()
        self.labels_state = {}

    def initUI(self):
        self.setWindowTitle(self.title)
        self.createTable()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

    def createTable(self):
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setSizeAdjustPolicy(
                QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setHorizontalHeaderLabels(['label', 'begin', 'end',
                                                    ''])
        self.tableWidget.setToolTip("Right click on a timestamp to set the player.")
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.viewport().installEventFilter(self)

    def new_mark(self, time, label):
        mode = self.__toggle_label_mode(label)
        if not mode:
            start_or_stop = 1
            index = self.tableWidget.rowCount()-1
            self.tableWidget.setItem(index, 0, QTableWidgetItem(str(label)))
            self.tableWidget.setItem(index, 2, QTableWidgetItem('...'))
            if not self.default_color:
                self.default_color = \
                        self.tableWidget.item(index, 0).background()
            self.tableWidget.insertRow(index+1)
        else:
            start_or_stop = 2
            matches = self.tableWidget.findItems(label, Qt.MatchExactly)
            index = matches[-1].row()
        timeItem = QTableWidgetItem(format_time(time))
        self.tableWidget.setItem(index, start_or_stop, timeItem)
        delButton = QPushButton()
        delButton.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delButton.clicked.connect(self.deleteRow)
        self.tableWidget.setCellWidget(index, 3, delButton)
        self.tableWidget.scrollToItem(timeItem)
        self.tableWidget.resizeColumnsToContents()
        self.set_row_color(index, mode)

    def new_mark_begin_end(self, label, begin, end):
        index = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(index, 0, QTableWidgetItem(str(label)))
        timeItemBegin = QTableWidgetItem(begin)
        timeItemEnd = QTableWidgetItem(end)
        self.tableWidget.setItem(index, 1, timeItemBegin)
        self.tableWidget.setItem(index, 2, timeItemEnd)
        delButton = QPushButton()
        delButton.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delButton.clicked.connect(self.deleteRow)
        self.tableWidget.setCellWidget(index, 3, delButton)
        self.tableWidget.scrollToItem(timeItemBegin)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.insertRow(index+1)

    def eventFilter(self, source, event):
        if(event.type() == QEvent.MouseButtonPress and
            event.buttons() == Qt.RightButton and
                source is self.tableWidget.viewport()):
            item = self.tableWidget.itemAt(event.pos())
            if item and item.column() in [1, 2]:
                position = str_to_ms(item.text())
                if position > 0:
                    self.control.setPosition(position)
        return super(LabelEditorWidget, self).eventFilter(source, event)

    @pyqtSlot()
    def deleteRow(self):
        button = self.sender()
        if button:
            row = self.tableWidget.indexAt(button.pos()).row()
            self.tableWidget.removeRow(row)

    def removeAllMarks(self):
        rows = self.tableWidget.rowCount()
        for row in range(0, rows - 1):
            self.tableWidget.removeRow(0)

    def set_row_color(self, index, mode):
        t = self.tableWidget
        if not mode:
            self.__row_colors(index, QColor(64, 249, 107))
        else:
            self.__row_colors(index, self.default_color)

    def get_marks(self):
        t = self.tableWidget
        marks = [[self.get_item_marks(i, j) for j in range(t.columnCount()-1)]
                 for i in range(t.rowCount()-1)]
        return marks

    def get_item_marks(self, i, j):
        try:
            return self.tableWidget.item(i, j).text()
        except:
            return 'ERROR_INVALID_VALUE'

    def __toggle_label_mode(self, label):
        if label not in self.labels_state:
            self.labels_state[label] = False
        mode = self.labels_state[label]
        self.labels_state[label] = not self.labels_state[label]
        return mode

    def __row_colors(self, i, color):
        for ii in range(self.tableWidget.columnCount()-1):
            self.tableWidget.item(i, ii).setBackground(color)

    def set_marks(self, marks):
        self.removeAllMarks()

        for line in marks:
            self.new_mark_begin_end(line[0], line[1], line[2])

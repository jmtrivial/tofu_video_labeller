from PyQt5.QtWidgets import (QLabel, QDialog, QFormLayout, QGroupBox,
        QPushButton, QSizePolicy, QStyle, QVBoxLayout, QWidget, QLineEdit,
        QTableWidget, QTableWidgetItem, QAction, QAbstractScrollArea, QFrame,
        QDialogButtonBox, QAbstractItemView)
from PyQt5.QtCore import pyqtSlot, Qt, QEvent
from PyQt5.QtGui import QIcon, QColor

from utils import format_time, str_to_ms

class LabelEditorWidget(QWidget):

    def __init__(self, control, groups):
        super(LabelEditorWidget, self).__init__()
        self.title = 'Label Editor'
        self.control = control
        self.groups = groups
        self.groups.changed.connect(self.update_incompatibilities)
        self.default_color = None
        self.active_color = QColor(64, 249, 107)
        self.default_text_color = None
        self.error_color = QColor(255, 0, 0)
        self.initUI()
        self.labels_state = {}


    def initUI(self):
        self.setWindowTitle(self.title)
        self.createTable()
        self.layout = QVBoxLayout()
        self.sortItems = QPushButton()
        self.sortItems.setEnabled(True)
        self.sortItems.setText("Sort")
        self.sortItems.clicked.connect(self.onSortItems)
        self.layout.addWidget(self.tableWidget)
        self.layout.addWidget(self.sortItems)
        self.setLayout(self.layout)

    def createTable(self):
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setSizeAdjustPolicy(
                QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setHorizontalHeaderLabels(['label', 'begin', 'end',
            ''])
        self.tableWidget.setToolTip("Right click on a timestamp to set the player.")
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.viewport().installEventFilter(self)
        self.tableWidget.selectionModel().currentChanged.connect(self.selection_changed)


    def selection_changed(self, sel1, sel2):
        row = sel1.row()
        begin, end = self.getBeginEndRow(row)
        if begin >= 0 and end != str_to_ms("199:59:59,999"):
            self.control.setActiveLabel(row, begin, end)
        else:
            self.control.unsetActiveLabel()


    def getBeginEndRow(self, row):
        s1 = str_to_ms(self.get_item_marks(row, 1))
        s2 = str_to_ms(self.get_item_marks(row, 2))
        if s2 < 0:
            s2 = str_to_ms("199:59:59,999")
        return (s1, s2)

    def isIntersectingRow(self, row1, row2):
        beg1, end1 = self.getBeginEndRow(row1)
        beg2, end2 = self.getBeginEndRow(row2)
        return (beg2 <= beg1 and beg1 < end2) or (beg2 < end1 and end1 <= end2) or (beg1 <= beg2 and beg2 < end1) or (beg1 < end2 and end2 <= end1)
        
    # assuming that row1 and row2 are not intersecting, it returns true if row1 is after row2
    def isAfterRow(self, row1, row2):
        beg1, end1 = self.getBeginEndRow(row1)
        beg2, end2 = self.getBeginEndRow(row2)
        
        return beg1 > beg2
        

    def toStringRow(self, rowid):
        return "(l:" + self.get_item_marks(rowid, 0) + ", s: " + self.get_item_marks(rowid, 1) + ", e: " + self.get_item_marks(rowid, 2) + ")"

    # return true if the current row is valid, i.e. if there is no intersection with another row in the same group
    # and if its predecessor in the same group is not in the list of incompatible intervals
    def isInvalidRow(self, rowid):
        labelName = self.get_item_marks(rowid, 0)
        groupName = self.groups.getGroupName(labelName)

        if groupName == "":
            return False
        
        pred = -1
        for rid2 in range(self.tableWidget.rowCount() - 1):
            if rid2 != rowid:
                l2 = self.get_item_marks(rid2, 0)
                group2 = self.groups.getGroupName(l2)
                if group2 == groupName:
                    if self.isIntersectingRow(rowid, rid2):
                        print("ERROR intersecting:", self.toStringRow(rid2), self.toStringRow(rowid))
                        return True
                    elif self.isAfterRow(rowid, rid2) and (pred == -1 or self.isAfterRow(rid2, pred)):
                        pred = rid2

        if pred != -1:
            l2 = self.get_item_marks(pred, 0)
            if self.groups.isIncompPred(labelName, l2):
                print("ERROR pred incompatibility:", self.toStringRow(pred), self.toStringRow(rowid))
                return True
        
        return False

    def update_incompatibilities(self):
        for rowid in range(self.tableWidget.rowCount() - 1):
            self.set_row_text_color(rowid, self.isInvalidRow(rowid)) 
        

    def set_default_colors(self, index):
        if not self.default_color:
            self.default_color = self.tableWidget.item(index, 0).background()
        if not self.default_text_color:
            self.default_text_color = self.tableWidget.item(index, 0).foreground()

    def new_mark(self, time, label):
        mode = self.__toggle_label_mode(label)
        if not mode:
            start_or_stop = 1
            index = self.tableWidget.rowCount()-1
            self.tableWidget.setItem(index, 0, QTableWidgetItem(str(label)))
            self.tableWidget.setItem(index, 2, QTableWidgetItem('...'))
            self.set_default_colors(index)
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
        self.update_incompatibilities()

    def new_mark_begin_end(self, label, begin, end):
        self.new_mark_begin_end_interface(label, begin, end)
        self.update_incompatibilities()

    def new_mark_begin_end_interface(self, label, begin, end):
        index = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(index, 0, QTableWidgetItem(str(label)))
        self.set_default_colors(index)
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

    def onSortItems(self):
        self.tableWidget.selectionModel().clearSelection()
        self.control.unsetActiveLabel()

        # load data
        entries = self.get_marks()
        
        # add supplementary values
        entries = [ e + [str_to_ms(e[1]), str_to_ms(e[2])] for e in entries]

        # sort data
        entries.sort(key=lambda row: row[3])
        
        # update data
        for i, e in enumerate(entries):
            self.highight_intersecting_item(i, False)
            for c in range(3):
                self.tableWidget.item(i, c).setText(e[c])
                
        self.update_incompatibilities()

    @pyqtSlot()
    def deleteRow(self):
        button = self.sender()
        if button:
            row = self.tableWidget.indexAt(button.pos()).row()
            self.__reset_label_mode(row)
            self.tableWidget.removeRow(row)
            self.update_incompatibilities()

    def removeAllMarks(self):
        rows = self.tableWidget.rowCount()
        for row in range(0, rows - 1):
            self.__reset_label_mode(0)
            self.tableWidget.removeRow(0)

    def set_row_text_color(self, index, mode):
        self.tableWidget.item(index, 0).setForeground(self.error_color if mode else self.default_text_color)

    def set_row_color(self, index, mode):
        if not mode:
            self.__row_colors(index, self.active_color)
        else:
            self.__row_colors(index, self.default_color)

    def get_marks(self):
        t = self.tableWidget
        marks = [[self.get_item_marks(i, j) for j in range(t.columnCount()-1)]\
                for i in range(t.rowCount()-1)]
        return marks

    def get_item_marks(self, i, j):
        try:
            return self.tableWidget.item(i, j).text()
        except:
            return 'ERROR_INVALID_VALUE'

    def __reset_label_mode(self, row):
        label = self.tableWidget.item(row, 0).text()
        if label in self.labels_state:
            self.labels_state[label] = False

    def __toggle_label_mode(self, label):
        if label not in self.labels_state:
            self.labels_state[label] = False
        mode = self.labels_state[label]
        self.labels_state[label] = not self.labels_state[label]
        return mode

    def __row_colors(self, i, color):
        for ii in range(self.tableWidget.columnCount()-1):
            if ii != 0:
                self.tableWidget.item(i, ii).setBackground(color)
    
    def highight_intersecting_items(self, ts):
        for ii in range(self.tableWidget.rowCount()):
            start = self.get_item_marks(ii, 1)
            end = self.get_item_marks(ii, 2)
            if start != "ERROR_INVALID_VALUE":
                startms = str_to_ms(start)
                if ts >= startms:
                    endms = str_to_ms(end)
                    self.highight_intersecting_item(ii, endms < 0 or ts <= endms)
                else:
                    self.highight_intersecting_item(ii, False)
    
    def highight_intersecting_item(self, index, intersecting):
        if intersecting:
            self.tableWidget.item(index, 0).setBackground(self.active_color)
        else:
            self.tableWidget.item(index, 0).setBackground(self.default_color)

    def set_marks(self, marks):
        self.removeAllMarks()

        for line in marks:
            self.new_mark_begin_end_interface(line[0], line[1], line[2])
        self.update_incompatibilities()

    def setStartMark(self, row, value):
        self.tableWidget.item(row, 1).setText(format_time(value))
        self.update_incompatibilities()


    def setEndMark(self, row, value):
        self.tableWidget.item(row, 2).setText(format_time(value))
        self.update_incompatibilities()

    def updateSelectedTimestamp(self, ts):
        tstext = format_time(ts)
        item = self.tableWidget.currentItem()
        if item != None:
            c = item.column()
            if c in [1, 2]:
                if c == 2:
                    i = str_to_ms(item.text())
                    if i <= ts:
                        item.setText(tstext)
                    else:
                        n = str_to_ms(self.tableWidget.item(item.row(), 1).text())
                        if n <= ts:
                            item.setText(tstext)
                else:
                    i = str_to_ms(item.text())
                    if i >= ts:
                        item.setText(tstext)
                    else:
                        n = str_to_ms(self.tableWidget.item(item.row(), 2).text())
                        if n < 0 or n >= ts:
                            item.setText(tstext)
            self.update_incompatibilities()








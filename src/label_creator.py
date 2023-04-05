from PyQt5.QtWidgets import (QLabel, QDialog, QFormLayout, QGroupBox,
        QPushButton, QSizePolicy, QStyle, QHBoxLayout, QVBoxLayout, QWidget, QLineEdit,
        QTableWidget, QTableWidgetItem, QAction, QAbstractScrollArea, QFrame,
        QDialogButtonBox, QKeySequenceEdit, QAbstractItemView, QFileDialog)
from PyQt5.QtCore import pyqtSlot, QDir, QUrl
from PyQt5.QtGui import QIcon, QIntValidator, QKeySequence
import csv

from signals import SignalBus

from group import LabelGroups

class LabelCreatorWidget(QWidget):

    def __init__(self):
        super(LabelCreatorWidget, self).__init__()
        self.title = 'Label Creator'
        self.comm = SignalBus.instance()
        self.groups = LabelGroups()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.createTable()
        self.createImportExportButtons()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.importExportButtons)
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)
        self.show()

    @pyqtSlot()
    def deleteRow(self):
        button = self.sender()
        if button:
            row = self.tableWidget.indexAt(button.pos()).row()
            self.deleteRowInternal(row)
            
    def deleteRowInternal(self, row):
        keySeqStr = self.tableWidget.item(row, 2).text()
        label = self.tableWidget.item(row, 1).text()
        self.groups.removeLabel(label)
        self.comm.delLabelSignal.emit(keySeqStr)
        self.tableWidget.removeRow(row)

    def createImportExportButtons(self):
        self.importExportButtons = QWidget()
        self.ieBLayout = QHBoxLayout()
        self.importExportButtons.setLayout(self.ieBLayout)
        self.importButton = QPushButton()
        self.importButton.setEnabled(True)
        self.importButton.setText("Import")
        self.ieBLayout.addWidget(self.importButton)
        self.exportButton = QPushButton()
        self.exportButton.setEnabled(True)
        self.exportButton.setText("Export")
        self.ieBLayout.addWidget(self.exportButton)
        
        self.exportButton.clicked.connect(self.exportLabels)
        self.importButton.clicked.connect(self.importLabels)

    def getLabels(self):
        labels = []
        rows = self.tableWidget.rowCount()
        for row in range(0, rows - 1):
            cellID = self.tableWidget.item(row, 0)
            cellLabel = self.tableWidget.item(row, 1)
            cellShortcut = self.tableWidget.item(row, 2)
            cellGroup = self.tableWidget.item(row, 4)
            cellPredIncomp = self.tableWidget.item(row, 5)
            labels.append([cellID.text(), cellLabel.text(), cellShortcut.text(), cellGroup.text(), cellPredIncomp.text()])
        return labels
    
    def updateLabels(self, labels):
        self.removeAllLabels()
        # add new labels to the interface
        entries = []
        for line in labels:
            if len(line) == 5:
                self.addLabelInterface(line[0], line[1], QKeySequence(line[2]), line[3], line[4])
            else:
                self.addLabelInterface(line[0], line[1], QKeySequence(line[2]))
            entries.append((line[1], line[3], line[4]))

        # add to the internal structure
        self.groups.addLabels(entries)
        
    def removeAllLabels(self):
        rows = self.tableWidget.rowCount()
        for row in range(0, rows - 1):
            self.deleteRowInternal(0)
        self.groups.clear()
        

    def exportLabels(self):
        fileUrl, _ = QFileDialog.getSaveFileUrl(self.importExportButtons, "Export labels", QUrl.fromLocalFile(QDir.homePath()), "CSV (*.csv)")
        fileName = fileUrl.toLocalFile()

        if fileName != '':
            with open(fileName, mode='w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
                labels = self.getLabels()
                writer.writerows(labels)

        
    def importLabels(self):
        fileUrl, _ = QFileDialog.getOpenFileUrl(self.importExportButtons, "Import labels", QUrl.fromLocalFile(QDir.homePath()), "CSV (*.csv)")
        fileName = fileUrl.toLocalFile()

        if fileName != '':
             with open(fileName, mode='r') as csv_file:
                labels = csv.reader(csv_file, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
                self.updateLabels(labels)

    def createTable(self):
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setSizeAdjustPolicy(
                QAbstractScrollArea.AdjustToContents)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setHorizontalHeaderLabels(['id', 'label',
            'shortcut', '', 'group', 'pred incompatibilities'])
        newButton = self._create_newButton()
        self.tableWidget.setCellWidget(0, 3, newButton)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    @pyqtSlot()
    def addLabel(self):
        newLabelDialog = NewLabelDialog()
        if newLabelDialog.exec_():
            lid = newLabelDialog.lid.text()
            label = newLabelDialog.label.text()
            keySeq = newLabelDialog.shortcut.keySequence()
            group = newLabelDialog.group.text()
            pred_incomp = newLabelDialog.pred_incomp.text()
            self.addLabelInternal(lid, label, keySeq, group, pred_incomp)
            
    def addLabelInternal(self, lid, label, keySeq, group = "", pred_incomp = ""):
        # set internal data
        self.groups.addLabel(label, group, pred_incomp)

        # set interface
        self.addLabelInterface(lid, label, keySeq, group, pred_incomp)
    
    def addLabelInterface(self, lid, label, keySeq, group = "", pred_incomp = ""):
        index = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(index, 0, QTableWidgetItem(lid))
        self.tableWidget.setItem(index, 1, QTableWidgetItem(label))
        keyItem = QTableWidgetItem(keySeq.toString())
        self.tableWidget.setItem(index, 2, keyItem)
        self.tableWidget.setItem(index, 4, QTableWidgetItem(group))
        self.tableWidget.setItem(index, 5, QTableWidgetItem(pred_incomp))
        delButton = QPushButton()
        delButton.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delButton.clicked.connect(self.deleteRow)
        self.tableWidget.setCellWidget(index, 3, delButton)
        self.tableWidget.scrollToItem(keyItem)
        self.comm.newLabelSignal.emit(keySeq, label)
        self.tableWidget.insertRow(index+1)
        newButton = self._create_newButton()
        self.tableWidget.setCellWidget(index+1, 3, newButton)
        self.tableWidget.resizeColumnsToContents()

    def _create_newButton(self):
        newButton = QPushButton()
        newButton.setIcon(self.style().standardIcon(
            QStyle.SP_FileDialogNewFolder))
        newButton.clicked.connect(self.addLabel)
        return newButton


class NewLabelDialog(QDialog):

    def __init__(self):
        super(NewLabelDialog, self).__init__()
        self.title = 'Add New Label'
        self.initUI()

    def initUI(self):
        self.createFormGroupBox()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        dialogLayout = QVBoxLayout()
        dialogLayout.addWidget(self.formGroupBox)
        dialogLayout.addWidget(buttonBox)
        self.setLayout(dialogLayout)
        self.setWindowTitle(self.title)

    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox('Label form')
        self.lid = QLineEdit()
        self.lid.setValidator(QIntValidator())
        self.label = QLineEdit()
        self.shortcut = QKeySequenceEdit()
        self.group = QLineEdit()
        self.pred_incomp = QLineEdit()
        layout = QFormLayout()
        layout.addRow(QLabel('id:'), self.lid)
        layout.addRow(QLabel('label:'), self.label)
        layout.addRow(QLabel('shortcut:'), self.shortcut)
        layout.addRow(QLabel('group:'), self.group)
        layout.addRow(QLabel('pred incompatibilities:'), self.pred_incomp)
        self.formGroupBox.setLayout(layout)



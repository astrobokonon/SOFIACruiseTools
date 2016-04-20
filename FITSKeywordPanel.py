# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FITSKeywordPanel.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(499, 391)
        Dialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonAdd = QtGui.QPushButton(Dialog)
        self.buttonAdd.setDefault(True)
        self.buttonAdd.setObjectName(_fromUtf8("buttonAdd"))
        self.gridLayout.addWidget(self.buttonAdd, 2, 2, 1, 1)
        self.buttonMovedown = QtGui.QPushButton(Dialog)
        self.buttonMovedown.setObjectName(_fromUtf8("buttonMovedown"))
        self.gridLayout.addWidget(self.buttonMovedown, 4, 2, 1, 1)
        self.spinboxCurrentHDU = QtGui.QSpinBox(Dialog)
        self.spinboxCurrentHDU.setAlignment(QtCore.Qt.AlignCenter)
        self.spinboxCurrentHDU.setSuffix(_fromUtf8(""))
        self.spinboxCurrentHDU.setObjectName(_fromUtf8("spinboxCurrentHDU"))
        self.gridLayout.addWidget(self.spinboxCurrentHDU, 0, 2, 1, 1)
        self.buttonRemove = QtGui.QPushButton(Dialog)
        self.buttonRemove.setObjectName(_fromUtf8("buttonRemove"))
        self.gridLayout.addWidget(self.buttonRemove, 5, 2, 1, 1)
        self.labelHDUchoosen = QtGui.QLabel(Dialog)
        self.labelHDUchoosen.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.labelHDUchoosen.setObjectName(_fromUtf8("labelHDUchoosen"))
        self.gridLayout.addWidget(self.labelHDUchoosen, 0, 0, 1, 2)
        self.buttonsApplyCancel = QtGui.QDialogButtonBox(Dialog)
        self.buttonsApplyCancel.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel)
        self.buttonsApplyCancel.setCenterButtons(True)
        self.buttonsApplyCancel.setObjectName(_fromUtf8("buttonsApplyCancel"))
        self.gridLayout.addWidget(self.buttonsApplyCancel, 7, 2, 1, 1)
        self.buttonMoveup = QtGui.QPushButton(Dialog)
        self.buttonMoveup.setObjectName(_fromUtf8("buttonMoveup"))
        self.gridLayout.addWidget(self.buttonMoveup, 3, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 1, 2, 1, 1)
        self.keywordListwidget = QtGui.QListWidget(Dialog)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.keywordListwidget.setFont(font)
        self.keywordListwidget.setSelectionRectVisible(True)
        self.keywordListwidget.setObjectName(_fromUtf8("keywordListwidget"))
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.keywordListwidget.addItem(item)
        self.gridLayout.addWidget(self.keywordListwidget, 1, 0, 8, 2)
        self.buttonLoad = QtGui.QPushButton(Dialog)
        self.buttonLoad.setObjectName(_fromUtf8("buttonLoad"))
        self.gridLayout.addWidget(self.buttonLoad, 9, 0, 1, 1)
        self.buttonSave = QtGui.QPushButton(Dialog)
        self.buttonSave.setObjectName(_fromUtf8("buttonSave"))
        self.gridLayout.addWidget(self.buttonSave, 9, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonsApplyCancel, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonsApplyCancel, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "FITS Keyword and HDU Selector", None))
        self.buttonAdd.setText(_translate("Dialog", "Add Keyword", None))
        self.buttonMovedown.setText(_translate("Dialog", "Move Down", None))
        self.buttonRemove.setText(_translate("Dialog", "Remove Keyword", None))
        self.labelHDUchoosen.setText(_translate("Dialog", "HDU to Search for Keywords (0 indexed)", None))
        self.buttonMoveup.setText(_translate("Dialog", "Move Up", None))
        __sortingEnabled = self.keywordListwidget.isSortingEnabled()
        self.keywordListwidget.setSortingEnabled(False)
        item = self.keywordListwidget.item(0)
        item.setText(_translate("Dialog", "DATE-OBS", None))
        item = self.keywordListwidget.item(1)
        item.setText(_translate("Dialog", "OBS_ID", None))
        item = self.keywordListwidget.item(2)
        item.setText(_translate("Dialog", "SPECTEL1", None))
        item = self.keywordListwidget.item(3)
        item.setText(_translate("Dialog", "SPECTEL2", None))
        item = self.keywordListwidget.item(4)
        item.setText(_translate("Dialog", "MISSN-ID", None))
        item = self.keywordListwidget.item(5)
        item.setText(_translate("Dialog", "DATASRC", None))
        item = self.keywordListwidget.item(6)
        item.setText(_translate("Dialog", "INSTRUME", None))
        self.keywordListwidget.setSortingEnabled(__sortingEnabled)
        self.buttonLoad.setText(_translate("Dialog", "Load List ...", None))
        self.buttonSave.setText(_translate("Dialog", "Save List ...", None))


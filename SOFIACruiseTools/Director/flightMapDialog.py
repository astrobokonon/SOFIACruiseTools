# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'flightMapDialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(731, 628)
        self.flightMap = MplWidget(Dialog)
        self.flightMap.setGeometry(QtCore.QRect(70, 60, 551, 471))
        self.flightMap.setObjectName("flightMap")
        self.plot_button = QtWidgets.QPushButton(Dialog)
        self.plot_button.setGeometry(QtCore.QRect(140, 550, 111, 51))
        self.plot_button.setObjectName("plot_button")
        self.clear_button = QtWidgets.QPushButton(Dialog)
        self.clear_button.setGeometry(QtCore.QRect(420, 550, 131, 51))
        self.clear_button.setObjectName("clear_button")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.plot_button.setText(_translate("Dialog", "Plot"))
        self.clear_button.setText(_translate("Dialog", "Clear"))

from mplwidget import MplWidget

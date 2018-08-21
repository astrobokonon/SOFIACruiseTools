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
        Dialog.resize(677, 747)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.flight_map_plot = MplWidget(Dialog)
        self.flight_map_plot.setGeometry(QtCore.QRect(10, 10, 641, 641))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.flight_map_plot.sizePolicy().hasHeightForWidth())
        self.flight_map_plot.setSizePolicy(sizePolicy)
        self.flight_map_plot.setObjectName("flight_map_plot")
        self.leg_selection_box = QtWidgets.QComboBox(Dialog)
        self.leg_selection_box.setGeometry(QtCore.QRect(30, 680, 79, 23))
        self.leg_selection_box.setObjectName("leg_selection_box")
        self.leg_label = QtWidgets.QLabel(Dialog)
        self.leg_label.setGeometry(QtCore.QRect(30, 660, 59, 15))
        self.leg_label.setObjectName("leg_label")
        self.time_selection = QtWidgets.QTimeEdit(Dialog)
        self.time_selection.setGeometry(QtCore.QRect(210, 680, 118, 24))
        self.time_selection.setObjectName("time_selection")
        self.time_label = QtWidgets.QLabel(Dialog)
        self.time_label.setGeometry(QtCore.QRect(210, 660, 59, 15))
        self.time_label.setObjectName("time_label")
        self.use_current = QtWidgets.QCheckBox(Dialog)
        self.use_current.setGeometry(QtCore.QRect(410, 680, 151, 20))
        self.use_current.setObjectName("use_current")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.leg_label.setText(_translate("Dialog", "Leg: "))
        self.time_label.setText(_translate("Dialog", "Time:"))
        self.use_current.setText(_translate("Dialog", "Use Current Time"))

from mplwidget import MplWidget

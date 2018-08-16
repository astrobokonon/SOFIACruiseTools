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
        Dialog.resize(897, 628)
        self.flight_map_plot = MplWidget(Dialog)
        self.flight_map_plot.setGeometry(QtCore.QRect(10, 10, 711, 521))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.flight_map_plot.sizePolicy().hasHeightForWidth())
        self.flight_map_plot.setSizePolicy(sizePolicy)
        self.flight_map_plot.setObjectName("flight_map_plot")
        self.plot_button = QtWidgets.QPushButton(Dialog)
        self.plot_button.setGeometry(QtCore.QRect(140, 550, 111, 51))
        self.plot_button.setObjectName("plot_button")
        self.clear_button = QtWidgets.QPushButton(Dialog)
        self.clear_button.setGeometry(QtCore.QRect(520, 550, 131, 51))
        self.clear_button.setObjectName("clear_button")
        self.plot_flight_button = QtWidgets.QPushButton(Dialog)
        self.plot_flight_button.setGeometry(QtCore.QRect(320, 550, 121, 51))
        self.plot_flight_button.setObjectName("plot_flight_button")
        self.leg_selection_box = QtWidgets.QComboBox(Dialog)
        self.leg_selection_box.setGeometry(QtCore.QRect(760, 70, 79, 23))
        self.leg_selection_box.setObjectName("leg_selection_box")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(760, 50, 59, 15))
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.plot_button.setText(_translate("Dialog", "Plot"))
        self.clear_button.setText(_translate("Dialog", "Clear"))
        self.plot_flight_button.setText(_translate("Dialog", "Plot Flight"))
        self.label.setText(_translate("Dialog", "Leg: "))

from mplwidget import MplWidget

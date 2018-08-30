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
        Dialog.resize(677, 778)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.flight_map_plot = MplWidget(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.flight_map_plot.sizePolicy().hasHeightForWidth())
        self.flight_map_plot.setSizePolicy(sizePolicy)
        self.flight_map_plot.setObjectName("flight_map_plot")
        self.gridLayout_2.addWidget(self.flight_map_plot, 0, 0, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.close_button = QtWidgets.QPushButton(Dialog)
        self.close_button.setEnabled(True)
        self.close_button.setAutoDefault(False)
        self.close_button.setObjectName("close_button")
        self.gridLayout.addWidget(self.close_button, 1, 5, 1, 1)
        self.use_current = QtWidgets.QCheckBox(Dialog)
        self.use_current.setChecked(True)
        self.use_current.setObjectName("use_current")
        self.gridLayout.addWidget(self.use_current, 2, 1, 1, 1)
        self.leg_completion_label = QtWidgets.QLabel(Dialog)
        self.leg_completion_label.setObjectName("leg_completion_label")
        self.gridLayout.addWidget(self.leg_completion_label, 1, 4, 1, 1)
        self.flight_completion_label = QtWidgets.QLabel(Dialog)
        self.flight_completion_label.setObjectName("flight_completion_label")
        self.gridLayout.addWidget(self.flight_completion_label, 2, 4, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 3, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 3, 1, 1)
        self.leg_label = QtWidgets.QLabel(Dialog)
        self.leg_label.setObjectName("leg_label")
        self.gridLayout.addWidget(self.leg_label, 0, 0, 1, 1)
        self.time_selection = QtWidgets.QTimeEdit(Dialog)
        self.time_selection.setWrapping(True)
        self.time_selection.setObjectName("time_selection")
        self.gridLayout.addWidget(self.time_selection, 1, 1, 1, 1)
        self.leg_selection_box = QtWidgets.QComboBox(Dialog)
        self.leg_selection_box.setObjectName("leg_selection_box")
        self.gridLayout.addWidget(self.leg_selection_box, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        self.time_label = QtWidgets.QLabel(Dialog)
        self.time_label.setObjectName("time_label")
        self.gridLayout.addWidget(self.time_label, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 3, 1, 1)
        self.current_leg_label = QtWidgets.QLabel(Dialog)
        self.current_leg_label.setObjectName("current_leg_label")
        self.gridLayout.addWidget(self.current_leg_label, 0, 4, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.close_button.setText(_translate("Dialog", "Close"))
        self.use_current.setText(_translate("Dialog", "Use Current Time"))
        self.leg_completion_label.setText(_translate("Dialog", "TextLabel"))
        self.flight_completion_label.setText(_translate("Dialog", "TextLabel"))
        self.label_2.setText(_translate("Dialog", "Flight Completion"))
        self.label.setText(_translate("Dialog", "Leg Completion:"))
        self.leg_label.setText(_translate("Dialog", "Leg: "))
        self.time_selection.setDisplayFormat(_translate("Dialog", "HH:mm:ss"))
        self.time_label.setText(_translate("Dialog", "Time:"))
        self.label_3.setText(_translate("Dialog", "Leg:"))
        self.current_leg_label.setText(_translate("Dialog", "TextLabel"))

from mplwidget import MplWidget

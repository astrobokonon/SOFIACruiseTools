# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'directorStartupDialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(720, 474)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(210, 430, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.titleText = QtWidgets.QLabel(Dialog)
        self.titleText.setGeometry(QtCore.QRect(80, 39, 361, 41))
        font = QtGui.QFont()
        font.setFamily("Abyssinica SIL")
        font.setPointSize(20)
        self.titleText.setFont(font)
        self.titleText.setObjectName("titleText")
        self.datalogText = QtWidgets.QLabel(Dialog)
        self.datalogText.setGeometry(QtCore.QRect(340, 250, 481, 16))
        self.datalogText.setObjectName("datalogText")
        self.datalocText = QtWidgets.QLabel(Dialog)
        self.datalocText.setGeometry(QtCore.QRect(340, 290, 481, 16))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.datalocText.sizePolicy().hasHeightForWidth())
        self.datalocText.setSizePolicy(sizePolicy)
        self.datalocText.setObjectName("datalocText")
        self.flightText = QtWidgets.QLabel(Dialog)
        self.flightText.setGeometry(QtCore.QRect(340, 120, 361, 16))
        self.flightText.setObjectName("flightText")
        self.logOutText = QtWidgets.QLabel(Dialog)
        self.logOutText.setGeometry(QtCore.QRect(340, 200, 321, 16))
        self.logOutText.setObjectName("logOutText")
        self.fitskwText = QtWidgets.QLabel(Dialog)
        self.fitskwText.setGeometry(QtCore.QRect(340, 330, 91, 16))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fitskwText.sizePolicy().hasHeightForWidth())
        self.fitskwText.setSizePolicy(sizePolicy)
        self.fitskwText.setObjectName("fitskwText")
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(50, 110, 106, 291))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.flightLabelText = QtWidgets.QLabel(self.layoutWidget)
        self.flightLabelText.setObjectName("flightLabelText")
        self.verticalLayout.addWidget(self.flightLabelText)
        self.InstLabelText = QtWidgets.QLabel(self.layoutWidget)
        self.InstLabelText.setObjectName("InstLabelText")
        self.verticalLayout.addWidget(self.InstLabelText)
        self.logOutLabelText = QtWidgets.QLabel(self.layoutWidget)
        self.logOutLabelText.setObjectName("logOutLabelText")
        self.verticalLayout.addWidget(self.logOutLabelText)
        self.datalogLabelText = QtWidgets.QLabel(self.layoutWidget)
        self.datalogLabelText.setObjectName("datalogLabelText")
        self.verticalLayout.addWidget(self.datalogLabelText)
        self.datalocLableText = QtWidgets.QLabel(self.layoutWidget)
        self.datalocLableText.setObjectName("datalocLableText")
        self.verticalLayout.addWidget(self.datalocLableText)
        self.fitskwLabelText = QtWidgets.QLabel(self.layoutWidget)
        self.fitskwLabelText.setObjectName("fitskwLabelText")
        self.verticalLayout.addWidget(self.fitskwLabelText)
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.layoutWidget1 = QtWidgets.QWidget(Dialog)
        self.layoutWidget1.setGeometry(QtCore.QRect(180, 100, 136, 311))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.flightButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.flightButton.setObjectName("flightButton")
        self.verticalLayout_2.addWidget(self.flightButton)
        self.instSelect = QtWidgets.QComboBox(self.layoutWidget1)
        self.instSelect.setObjectName("instSelect")
        self.instSelect.addItem("")
        self.instSelect.addItem("")
        self.instSelect.addItem("")
        self.instSelect.addItem("")
        self.verticalLayout_2.addWidget(self.instSelect)
        self.logOutButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.logOutButton.setObjectName("logOutButton")
        self.verticalLayout_2.addWidget(self.logOutButton)
        self.datalogButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.datalogButton.setObjectName("datalogButton")
        self.verticalLayout_2.addWidget(self.datalogButton)
        self.datalocButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.datalocButton.setObjectName("datalocButton")
        self.verticalLayout_2.addWidget(self.datalocButton)
        self.fitkwButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.fitkwButton.setObjectName("fitkwButton")
        self.verticalLayout_2.addWidget(self.fitkwButton)
        self.timezoneSelect = QtWidgets.QComboBox(self.layoutWidget1)
        self.timezoneSelect.setObjectName("timezoneSelect")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.timezoneSelect.addItem("")
        self.verticalLayout_2.addWidget(self.timezoneSelect)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.titleText.setText(_translate("Dialog", "SOFIA Cruise Director Setup"))
        self.datalogText.setText(_translate("Dialog", "Not Set"))
        self.datalocText.setText(_translate("Dialog", "Not Set"))
        self.flightText.setText(_translate("Dialog", "Not Set"))
        self.logOutText.setText(_translate("Dialog", "Not Set"))
        self.fitskwText.setText(_translate("Dialog", "Default"))
        self.flightLabelText.setText(_translate("Dialog", "Flight Plan"))
        self.InstLabelText.setText(_translate("Dialog", "Instrument"))
        self.logOutLabelText.setText(_translate("Dialog", "<html><head/><body><p>Log Output (<span style=\" color:#ff0000;\">*</span>)</p></body></html>"))
        self.datalogLabelText.setText(_translate("Dialog", "Data Log Output "))
        self.datalocLableText.setText(_translate("Dialog", "Data Location"))
        self.fitskwLabelText.setText(_translate("Dialog", "FITS Keywords"))
        self.label.setText(_translate("Dialog", "Local Time Zone"))
        self.flightButton.setText(_translate("Dialog", "Select"))
        self.instSelect.setItemText(0, _translate("Dialog", "HAWC+"))
        self.instSelect.setItemText(1, _translate("Dialog", "FORCAST"))
        self.instSelect.setItemText(2, _translate("Dialog", "FIFI-LS"))
        self.instSelect.setItemText(3, _translate("Dialog", "EXES"))
        self.logOutButton.setText(_translate("Dialog", "Select "))
        self.datalogButton.setText(_translate("Dialog", "Select "))
        self.datalocButton.setText(_translate("Dialog", "Select "))
        self.fitkwButton.setText(_translate("Dialog", "Select"))
        self.timezoneSelect.setItemText(0, _translate("Dialog", "US/Pacific"))
        self.timezoneSelect.setItemText(1, _translate("Dialog", "US/Hawaii"))
        self.timezoneSelect.setItemText(2, _translate("Dialog", "US/Alaska"))
        self.timezoneSelect.setItemText(3, _translate("Dialog", "US/Eastern"))
        self.timezoneSelect.setItemText(4, _translate("Dialog", "US/Central"))
        self.timezoneSelect.setItemText(5, _translate("Dialog", "US/Mountain"))
        self.timezoneSelect.setItemText(6, _translate("Dialog", "UTC"))
        self.timezoneSelect.setItemText(7, _translate("Dialog", "Pacific/Auckland"))


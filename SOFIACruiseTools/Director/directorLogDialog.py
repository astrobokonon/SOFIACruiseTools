# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'directorLogDialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(753, 275)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.local_takeoff = QtWidgets.QPushButton(Dialog)
        self.local_takeoff.setAutoDefault(False)
        self.local_takeoff.setObjectName("local_takeoff")
        self.gridLayout.addWidget(self.local_takeoff, 0, 0, 1, 1)
        self.local_on_heading = QtWidgets.QPushButton(Dialog)
        self.local_on_heading.setAutoDefault(False)
        self.local_on_heading.setObjectName("local_on_heading")
        self.gridLayout.addWidget(self.local_on_heading, 0, 1, 1, 1)
        self.local_on_target = QtWidgets.QPushButton(Dialog)
        self.local_on_target.setAutoDefault(False)
        self.local_on_target.setObjectName("local_on_target")
        self.gridLayout.addWidget(self.local_on_target, 0, 2, 1, 1)
        self.local_turning = QtWidgets.QPushButton(Dialog)
        self.local_turning.setAutoDefault(False)
        self.local_turning.setObjectName("local_turning")
        self.gridLayout.addWidget(self.local_turning, 0, 3, 1, 1)
        self.local_fault_mccs = QtWidgets.QPushButton(Dialog)
        self.local_fault_mccs.setAutoDefault(False)
        self.local_fault_mccs.setObjectName("local_fault_mccs")
        self.gridLayout.addWidget(self.local_fault_mccs, 0, 4, 1, 1)
        self.local_fault_si = QtWidgets.QPushButton(Dialog)
        self.local_fault_si.setAutoDefault(False)
        self.local_fault_si.setObjectName("local_fault_si")
        self.gridLayout.addWidget(self.local_fault_si, 0, 5, 1, 1)
        self.local_landing = QtWidgets.QPushButton(Dialog)
        self.local_landing.setAutoDefault(False)
        self.local_landing.setObjectName("local_landing")
        self.gridLayout.addWidget(self.local_landing, 0, 6, 1, 1)
        self.local_ignore = QtWidgets.QPushButton(Dialog)
        self.local_ignore.setAutoDefault(False)
        self.local_ignore.setObjectName("local_ignore")
        self.gridLayout.addWidget(self.local_ignore, 0, 7, 1, 1)
        self.local_display = QtWidgets.QTextEdit(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_display.sizePolicy().hasHeightForWidth())
        self.local_display.setSizePolicy(sizePolicy)
        self.local_display.setReadOnly(True)
        self.local_display.setObjectName("local_display")
        self.gridLayout.addWidget(self.local_display, 1, 0, 1, 8)
        self.local_input_line = QtWidgets.QLineEdit(Dialog)
        self.local_input_line.setObjectName("local_input_line")
        self.gridLayout.addWidget(self.local_input_line, 2, 0, 1, 6)
        self.local_post = QtWidgets.QPushButton(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_post.sizePolicy().hasHeightForWidth())
        self.local_post.setSizePolicy(sizePolicy)
        self.local_post.setAutoDefault(True)
        self.local_post.setObjectName("local_post")
        self.gridLayout.addWidget(self.local_post, 2, 6, 1, 1)
        self.close_button = QtWidgets.QPushButton(Dialog)
        self.close_button.setAutoDefault(False)
        self.close_button.setObjectName("close_button")
        self.gridLayout.addWidget(self.close_button, 2, 7, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.local_takeoff.setText(_translate("Dialog", "Takeoff"))
        self.local_on_heading.setText(_translate("Dialog", "On Heading"))
        self.local_on_target.setText(_translate("Dialog", "On Target"))
        self.local_turning.setText(_translate("Dialog", "Turning"))
        self.local_fault_mccs.setText(_translate("Dialog", "MCCS Problem"))
        self.local_fault_si.setText(_translate("Dialog", "SI Problem"))
        self.local_landing.setText(_translate("Dialog", "Landing"))
        self.local_ignore.setText(_translate("Dialog", "Ignore Last Line"))
        self.local_display.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.Lucida Grande UI\'; font-size:13pt;\"><br /></p></body></html>"))
        self.local_post.setText(_translate("Dialog", "Post"))
        self.close_button.setText(_translate("Dialog", "Close"))


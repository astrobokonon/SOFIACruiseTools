# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'directorLogDialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(753, 275)
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setGeometry(QtCore.QRect(11, 11, 728, 252))
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.local_takeoff = QtWidgets.QPushButton(self.widget)
        self.local_takeoff.setAutoDefault(False)
        self.local_takeoff.setObjectName("local_takeoff")
        self.gridLayout.addWidget(self.local_takeoff, 0, 0, 1, 1)
        self.local_on_heading = QtWidgets.QPushButton(self.widget)
        self.local_on_heading.setAutoDefault(False)
        self.local_on_heading.setObjectName("local_on_heading")
        self.gridLayout.addWidget(self.local_on_heading, 0, 1, 1, 1)
        self.local_on_target = QtWidgets.QPushButton(self.widget)
        self.local_on_target.setAutoDefault(False)
        self.local_on_target.setObjectName("local_on_target")
        self.gridLayout.addWidget(self.local_on_target, 0, 2, 1, 1)
        self.local_turning = QtWidgets.QPushButton(self.widget)
        self.local_turning.setAutoDefault(False)
        self.local_turning.setObjectName("local_turning")
        self.gridLayout.addWidget(self.local_turning, 0, 3, 1, 1)
        self.local_fault_mccs = QtWidgets.QPushButton(self.widget)
        self.local_fault_mccs.setAutoDefault(False)
        self.local_fault_mccs.setObjectName("local_fault_mccs")
        self.gridLayout.addWidget(self.local_fault_mccs, 0, 4, 1, 1)
        self.local_fault_si = QtWidgets.QPushButton(self.widget)
        self.local_fault_si.setAutoDefault(False)
        self.local_fault_si.setObjectName("local_fault_si")
        self.gridLayout.addWidget(self.local_fault_si, 0, 5, 1, 1)
        self.local_landing = QtWidgets.QPushButton(self.widget)
        self.local_landing.setAutoDefault(False)
        self.local_landing.setObjectName("local_landing")
        self.gridLayout.addWidget(self.local_landing, 0, 6, 1, 1)
        self.local_ignore = QtWidgets.QPushButton(self.widget)
        self.local_ignore.setAutoDefault(False)
        self.local_ignore.setObjectName("local_ignore")
        self.gridLayout.addWidget(self.local_ignore, 0, 7, 1, 1)
        self.local_post = QtWidgets.QPushButton(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_post.sizePolicy().hasHeightForWidth())
        self.local_post.setSizePolicy(sizePolicy)
        self.local_post.setAutoDefault(False)
        self.local_post.setObjectName("local_post")
        self.gridLayout.addWidget(self.local_post, 2, 7, 1, 1)
        self.local_display = QtWidgets.QTextEdit(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_display.sizePolicy().hasHeightForWidth())
        self.local_display.setSizePolicy(sizePolicy)
        self.local_display.setReadOnly(True)
        self.local_display.setObjectName("local_display")
        self.gridLayout.addWidget(self.local_display, 1, 0, 1, 8)
        self.local_input_line = QtWidgets.QLineEdit(self.widget)
        self.local_input_line.setObjectName("local_input_line")
        self.gridLayout.addWidget(self.local_input_line, 2, 0, 1, 7)

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
        self.local_post.setText(_translate("Dialog", "Post"))
        self.local_display.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.Lucida Grande UI\'; font-size:13pt;\"><br /></p></body></html>"))


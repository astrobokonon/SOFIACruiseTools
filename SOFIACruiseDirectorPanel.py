# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SOFIACruiseDirectorPanel.ui'
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1101, 830)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.groupBox_2 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(self.groupBox_2)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.directorLogTab = QtGui.QWidget()
        self.directorLogTab.setObjectName(_fromUtf8("directorLogTab"))
        self.gridLayout_10 = QtGui.QGridLayout(self.directorLogTab)
        self.gridLayout_10.setObjectName(_fromUtf8("gridLayout_10"))
        self.log_quick_takeoff = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_takeoff.setObjectName(_fromUtf8("log_quick_takeoff"))
        self.gridLayout_10.addWidget(self.log_quick_takeoff, 0, 0, 1, 1)
        self.log_quick_onheading = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_onheading.setObjectName(_fromUtf8("log_quick_onheading"))
        self.gridLayout_10.addWidget(self.log_quick_onheading, 0, 1, 1, 1)
        self.log_quick_ontarget = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_ontarget.setObjectName(_fromUtf8("log_quick_ontarget"))
        self.gridLayout_10.addWidget(self.log_quick_ontarget, 0, 2, 1, 1)
        self.log_quick_turning = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_turning.setObjectName(_fromUtf8("log_quick_turning"))
        self.gridLayout_10.addWidget(self.log_quick_turning, 0, 3, 1, 1)
        self.log_quick_faultmccs = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_faultmccs.setObjectName(_fromUtf8("log_quick_faultmccs"))
        self.gridLayout_10.addWidget(self.log_quick_faultmccs, 0, 4, 1, 1)
        self.log_quick_faultsi = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_faultsi.setObjectName(_fromUtf8("log_quick_faultsi"))
        self.gridLayout_10.addWidget(self.log_quick_faultsi, 0, 5, 1, 1)
        self.log_quick_landing = QtGui.QPushButton(self.directorLogTab)
        self.log_quick_landing.setObjectName(_fromUtf8("log_quick_landing"))
        self.gridLayout_10.addWidget(self.log_quick_landing, 0, 6, 1, 2)
        self.log_save = QtGui.QPushButton(self.directorLogTab)
        self.log_save.setObjectName(_fromUtf8("log_save"))
        self.gridLayout_10.addWidget(self.log_save, 0, 8, 1, 1)
        self.log_display = QtGui.QTextEdit(self.directorLogTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.log_display.sizePolicy().hasHeightForWidth())
        self.log_display.setSizePolicy(sizePolicy)
        self.log_display.setReadOnly(True)
        self.log_display.setObjectName(_fromUtf8("log_display"))
        self.gridLayout_10.addWidget(self.log_display, 1, 0, 1, 9)
        self.log_inputline = QtGui.QLineEdit(self.directorLogTab)
        self.log_inputline.setObjectName(_fromUtf8("log_inputline"))
        self.gridLayout_10.addWidget(self.log_inputline, 2, 0, 1, 7)
        self.log_post = QtGui.QPushButton(self.directorLogTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.log_post.sizePolicy().hasHeightForWidth())
        self.log_post.setSizePolicy(sizePolicy)
        self.log_post.setObjectName(_fromUtf8("log_post"))
        self.gridLayout_10.addWidget(self.log_post, 2, 7, 1, 1)
        self.txt_logoutputname = QtGui.QLabel(self.directorLogTab)
        font = QtGui.QFont()
        font.setItalic(True)
        self.txt_logoutputname.setFont(font)
        self.txt_logoutputname.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_logoutputname.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.txt_logoutputname.setObjectName(_fromUtf8("txt_logoutputname"))
        self.gridLayout_10.addWidget(self.txt_logoutputname, 2, 8, 1, 1)
        self.tabWidget.addTab(self.directorLogTab, _fromUtf8(""))
        self.dataLogTab = QtGui.QWidget()
        self.dataLogTab.setObjectName(_fromUtf8("dataLogTab"))
        self.gridLayout_3 = QtGui.QGridLayout(self.dataLogTab)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.table_datalog = QtGui.QTableWidget(self.dataLogTab)
        self.table_datalog.setFrameShape(QtGui.QFrame.StyledPanel)
        self.table_datalog.setAlternatingRowColors(True)
        self.table_datalog.setObjectName(_fromUtf8("table_datalog"))
        self.table_datalog.setColumnCount(0)
        self.table_datalog.setRowCount(0)
        self.gridLayout_3.addWidget(self.table_datalog, 8, 0, 1, 4)
        self.datalog_savefile = QtGui.QPushButton(self.dataLogTab)
        self.datalog_savefile.setObjectName(_fromUtf8("datalog_savefile"))
        self.gridLayout_3.addWidget(self.datalog_savefile, 2, 0, 1, 1)
        self.datalog_opendir = QtGui.QPushButton(self.dataLogTab)
        self.datalog_opendir.setObjectName(_fromUtf8("datalog_opendir"))
        self.gridLayout_3.addWidget(self.datalog_opendir, 0, 0, 1, 1)
        self.datalog_autoupdate = QtGui.QCheckBox(self.dataLogTab)
        self.datalog_autoupdate.setChecked(True)
        self.datalog_autoupdate.setObjectName(_fromUtf8("datalog_autoupdate"))
        self.gridLayout_3.addWidget(self.datalog_autoupdate, 0, 3, 1, 1)
        self.txt_datalogdir = QtGui.QLabel(self.dataLogTab)
        font = QtGui.QFont()
        font.setItalic(True)
        self.txt_datalogdir.setFont(font)
        self.txt_datalogdir.setText(_fromUtf8(""))
        self.txt_datalogdir.setObjectName(_fromUtf8("txt_datalogdir"))
        self.gridLayout_3.addWidget(self.txt_datalogdir, 0, 1, 1, 2)
        self.datalog_updateinterval = QtGui.QSpinBox(self.dataLogTab)
        self.datalog_updateinterval.setAlignment(QtCore.Qt.AlignCenter)
        self.datalog_updateinterval.setProperty("value", 5)
        self.datalog_updateinterval.setObjectName(_fromUtf8("datalog_updateinterval"))
        self.gridLayout_3.addWidget(self.datalog_updateinterval, 2, 3, 1, 1)
        self.txt_datalogsavefile = QtGui.QLabel(self.dataLogTab)
        font = QtGui.QFont()
        font.setItalic(True)
        self.txt_datalogsavefile.setFont(font)
        self.txt_datalogsavefile.setText(_fromUtf8(""))
        self.txt_datalogsavefile.setObjectName(_fromUtf8("txt_datalogsavefile"))
        self.gridLayout_3.addWidget(self.txt_datalogsavefile, 2, 1, 1, 2)
        self.datalog_forceupdate = QtGui.QPushButton(self.dataLogTab)
        self.datalog_forceupdate.setObjectName(_fromUtf8("datalog_forceupdate"))
        self.gridLayout_3.addWidget(self.datalog_forceupdate, 9, 0, 1, 1)
        self.datalog_forcewrite = QtGui.QPushButton(self.dataLogTab)
        self.datalog_forcewrite.setObjectName(_fromUtf8("datalog_forcewrite"))
        self.gridLayout_3.addWidget(self.datalog_forcewrite, 9, 1, 1, 1)
        self.datalog_editFITSKeys = QtGui.QPushButton(self.dataLogTab)
        self.datalog_editFITSKeys.setObjectName(_fromUtf8("datalog_editFITSKeys"))
        self.gridLayout_3.addWidget(self.datalog_editFITSKeys, 9, 2, 1, 2)
        self.tabWidget.addTab(self.dataLogTab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabWidget)
        self.gridLayout.addWidget(self.groupBox_2, 2, 0, 1, 5)
        self.LegTimers = QtGui.QGroupBox(self.centralwidget)
        self.LegTimers.setObjectName(_fromUtf8("LegTimers"))
        self.gridLayout_2 = QtGui.QGridLayout(self.LegTimers)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.widget = QtGui.QWidget(self.LegTimers)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.gridLayout_8 = QtGui.QGridLayout(self.widget)
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.leg_timer_stop = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leg_timer_stop.sizePolicy().hasHeightForWidth())
        self.leg_timer_stop.setSizePolicy(sizePolicy)
        self.leg_timer_stop.setObjectName(_fromUtf8("leg_timer_stop"))
        self.gridLayout_8.addWidget(self.leg_timer_stop, 0, 1, 1, 1)
        self.leg_timer_reset = QtGui.QPushButton(self.widget)
        self.leg_timer_reset.setObjectName(_fromUtf8("leg_timer_reset"))
        self.gridLayout_8.addWidget(self.leg_timer_reset, 1, 0, 1, 2)
        self.leg_timer_start = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leg_timer_start.sizePolicy().hasHeightForWidth())
        self.leg_timer_start.setSizePolicy(sizePolicy)
        self.leg_timer_start.setObjectName(_fromUtf8("leg_timer_start"))
        self.gridLayout_8.addWidget(self.leg_timer_start, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.widget, 3, 0, 1, 1)
        self.widget_2 = QtGui.QWidget(self.LegTimers)
        self.widget_2.setObjectName(_fromUtf8("widget_2"))
        self.gridLayout_9 = QtGui.QGridLayout(self.widget_2)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        self.time_select_remaining = QtGui.QRadioButton(self.widget_2)
        self.time_select_remaining.setChecked(True)
        self.time_select_remaining.setObjectName(_fromUtf8("time_select_remaining"))
        self.gridLayout_9.addWidget(self.time_select_remaining, 0, 0, 1, 1)
        self.time_select_elapsed = QtGui.QRadioButton(self.widget_2)
        self.time_select_elapsed.setChecked(False)
        self.time_select_elapsed.setObjectName(_fromUtf8("time_select_elapsed"))
        self.gridLayout_9.addWidget(self.time_select_elapsed, 0, 1, 1, 1)
        self.leg_duration = QtGui.QTimeEdit(self.widget_2)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.leg_duration.setFont(font)
        self.leg_duration.setAlignment(QtCore.Qt.AlignCenter)
        self.leg_duration.setDateTime(QtCore.QDateTime(QtCore.QDate(2000, 1, 1), QtCore.QTime(0, 0, 0)))
        self.leg_duration.setCurrentSection(QtGui.QDateTimeEdit.HourSection)
        self.leg_duration.setTimeSpec(QtCore.Qt.LocalTime)
        self.leg_duration.setObjectName(_fromUtf8("leg_duration"))
        self.gridLayout_9.addWidget(self.leg_duration, 3, 0, 1, 2)
        self.txt_leg_duration = QtGui.QLabel(self.widget_2)
        self.txt_leg_duration.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_leg_duration.setObjectName(_fromUtf8("txt_leg_duration"))
        self.gridLayout_9.addWidget(self.txt_leg_duration, 2, 0, 1, 2)
        self.gridLayout_2.addWidget(self.widget_2, 2, 0, 1, 1)
        self.txt_leg_timer = QtGui.QLabel(self.LegTimers)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Digital-7"))
        font.setPointSize(70)
        self.txt_leg_timer.setFont(font)
        self.txt_leg_timer.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_leg_timer.setObjectName(_fromUtf8("txt_leg_timer"))
        self.gridLayout_2.addWidget(self.txt_leg_timer, 0, 0, 2, 1)
        self.gridLayout.addWidget(self.LegTimers, 0, 3, 2, 2)
        self.LegInformation = QtGui.QGroupBox(self.centralwidget)
        self.LegInformation.setObjectName(_fromUtf8("LegInformation"))
        self.gridLayout_4 = QtGui.QGridLayout(self.LegInformation)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.leg_next = QtGui.QPushButton(self.LegInformation)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leg_next.sizePolicy().hasHeightForWidth())
        self.leg_next.setSizePolicy(sizePolicy)
        self.leg_next.setObjectName(_fromUtf8("leg_next"))
        self.gridLayout_4.addWidget(self.leg_next, 2, 2, 1, 1)
        self.leg_previous = QtGui.QPushButton(self.LegInformation)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leg_previous.sizePolicy().hasHeightForWidth())
        self.leg_previous.setSizePolicy(sizePolicy)
        self.leg_previous.setObjectName(_fromUtf8("leg_previous"))
        self.gridLayout_4.addWidget(self.leg_previous, 2, 0, 1, 1)
        self.widget_3 = QtGui.QWidget(self.LegInformation)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy)
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.gridlayout = QtGui.QGridLayout(self.widget_3)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.landing_time = QtGui.QDateTimeEdit(self.widget_3)
        self.landing_time.setAlignment(QtCore.Qt.AlignCenter)
        self.landing_time.setObjectName(_fromUtf8("landing_time"))
        self.gridlayout.addWidget(self.landing_time, 2, 1, 1, 1)
        self.set_landingFP = QtGui.QCheckBox(self.widget_3)
        self.set_landingFP.setChecked(True)
        self.set_landingFP.setObjectName(_fromUtf8("set_landingFP"))
        self.gridlayout.addWidget(self.set_landingFP, 2, 0, 1, 1)
        self.set_takeoffFP = QtGui.QCheckBox(self.widget_3)
        self.set_takeoffFP.setChecked(True)
        self.set_takeoffFP.setObjectName(_fromUtf8("set_takeoffFP"))
        self.gridlayout.addWidget(self.set_takeoffFP, 1, 0, 1, 1)
        self.takeoff_time = QtGui.QDateTimeEdit(self.widget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.takeoff_time.sizePolicy().hasHeightForWidth())
        self.takeoff_time.setSizePolicy(sizePolicy)
        self.takeoff_time.setAlignment(QtCore.Qt.AlignCenter)
        self.takeoff_time.setObjectName(_fromUtf8("takeoff_time"))
        self.gridlayout.addWidget(self.takeoff_time, 1, 1, 1, 1)
        self.flightplan_filename = QtGui.QLabel(self.widget_3)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.flightplan_filename.setFont(font)
        self.flightplan_filename.setAlignment(QtCore.Qt.AlignCenter)
        self.flightplan_filename.setObjectName(_fromUtf8("flightplan_filename"))
        self.gridlayout.addWidget(self.flightplan_filename, 0, 0, 1, 1)
        self.flightplan_openfile = QtGui.QPushButton(self.widget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.flightplan_openfile.sizePolicy().hasHeightForWidth())
        self.flightplan_openfile.setSizePolicy(sizePolicy)
        self.flightplan_openfile.setAutoDefault(True)
        self.flightplan_openfile.setObjectName(_fromUtf8("flightplan_openfile"))
        self.gridlayout.addWidget(self.flightplan_openfile, 0, 1, 1, 1)
        self.gridLayout_4.addWidget(self.widget_3, 0, 0, 1, 3)
        self.leg_details = QtGui.QWidget(self.LegInformation)
        self.leg_details.setObjectName(_fromUtf8("leg_details"))
        self.gridLayout_6 = QtGui.QGridLayout(self.leg_details)
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.txt_elevation = QtGui.QLabel(self.leg_details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_elevation.sizePolicy().hasHeightForWidth())
        self.txt_elevation.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.txt_elevation.setFont(font)
        self.txt_elevation.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_elevation.setObjectName(_fromUtf8("txt_elevation"))
        self.gridLayout_6.addWidget(self.txt_elevation, 3, 0, 1, 1)
        self.leg_rofrofrt = QtGui.QLabel(self.leg_details)
        self.leg_rofrofrt.setText(_fromUtf8(""))
        self.leg_rofrofrt.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.leg_rofrofrt.setObjectName(_fromUtf8("leg_rofrofrt"))
        self.gridLayout_6.addWidget(self.leg_rofrofrt, 4, 1, 1, 1)
        self.leg_elevation = QtGui.QLabel(self.leg_details)
        self.leg_elevation.setText(_fromUtf8(""))
        self.leg_elevation.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.leg_elevation.setObjectName(_fromUtf8("leg_elevation"))
        self.gridLayout_6.addWidget(self.leg_elevation, 3, 1, 1, 1)
        self.leg_obsblock = QtGui.QLabel(self.leg_details)
        self.leg_obsblock.setText(_fromUtf8(""))
        self.leg_obsblock.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.leg_obsblock.setObjectName(_fromUtf8("leg_obsblock"))
        self.gridLayout_6.addWidget(self.leg_obsblock, 5, 1, 1, 1)
        self.txt_leg = QtGui.QLabel(self.leg_details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_leg.sizePolicy().hasHeightForWidth())
        self.txt_leg.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.txt_leg.setFont(font)
        self.txt_leg.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_leg.setObjectName(_fromUtf8("txt_leg"))
        self.gridLayout_6.addWidget(self.txt_leg, 1, 0, 1, 1)
        self.txt_rof = QtGui.QLabel(self.leg_details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_rof.sizePolicy().hasHeightForWidth())
        self.txt_rof.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.txt_rof.setFont(font)
        self.txt_rof.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_rof.setObjectName(_fromUtf8("txt_rof"))
        self.gridLayout_6.addWidget(self.txt_rof, 4, 0, 1, 1)
        self.leg_number = QtGui.QLabel(self.leg_details)
        self.leg_number.setText(_fromUtf8(""))
        self.leg_number.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.leg_number.setObjectName(_fromUtf8("leg_number"))
        self.gridLayout_6.addWidget(self.leg_number, 1, 1, 1, 1)
        self.txt_obsplan = QtGui.QLabel(self.leg_details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_obsplan.sizePolicy().hasHeightForWidth())
        self.txt_obsplan.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.txt_obsplan.setFont(font)
        self.txt_obsplan.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_obsplan.setObjectName(_fromUtf8("txt_obsplan"))
        self.gridLayout_6.addWidget(self.txt_obsplan, 5, 0, 1, 1)
        self.leg_target = QtGui.QLabel(self.leg_details)
        self.leg_target.setText(_fromUtf8(""))
        self.leg_target.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.leg_target.setObjectName(_fromUtf8("leg_target"))
        self.gridLayout_6.addWidget(self.leg_target, 2, 1, 1, 1)
        self.txt_target = QtGui.QLabel(self.leg_details)
        self.txt_target.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_target.sizePolicy().hasHeightForWidth())
        self.txt_target.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.txt_target.setFont(font)
        self.txt_target.setLineWidth(1)
        self.txt_target.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_target.setObjectName(_fromUtf8("txt_target"))
        self.gridLayout_6.addWidget(self.txt_target, 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.leg_details, 1, 0, 1, 3)
        self.gridLayout.addWidget(self.LegInformation, 0, 0, 2, 2)
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBox)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.set_takeoff_time = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.set_takeoff_time.sizePolicy().hasHeightForWidth())
        self.set_takeoff_time.setSizePolicy(sizePolicy)
        self.set_takeoff_time.setObjectName(_fromUtf8("set_takeoff_time"))
        self.gridLayout_7.addWidget(self.set_takeoff_time, 2, 0, 1, 1)
        self.set_landing_time = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.set_landing_time.sizePolicy().hasHeightForWidth())
        self.set_landing_time.setSizePolicy(sizePolicy)
        self.set_landing_time.setCheckable(False)
        self.set_landing_time.setFlat(False)
        self.set_landing_time.setObjectName(_fromUtf8("set_landing_time"))
        self.gridLayout_7.addWidget(self.set_landing_time, 2, 1, 1, 1)
        self.set_takeofflanding = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.set_takeofflanding.sizePolicy().hasHeightForWidth())
        self.set_takeofflanding.setSizePolicy(sizePolicy)
        self.set_takeofflanding.setObjectName(_fromUtf8("set_takeofflanding"))
        self.gridLayout_7.addWidget(self.set_takeofflanding, 2, 2, 1, 1)
        self.txt_ttl = QtGui.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Digital-7"))
        font.setPointSize(50)
        self.txt_ttl.setFont(font)
        self.txt_ttl.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_ttl.setObjectName(_fromUtf8("txt_ttl"))
        self.gridLayout_7.addWidget(self.txt_ttl, 1, 0, 1, 3)
        self.txt_met = QtGui.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Digital-7"))
        font.setPointSize(50)
        self.txt_met.setFont(font)
        self.txt_met.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_met.setObjectName(_fromUtf8("txt_met"))
        self.gridLayout_7.addWidget(self.txt_met, 0, 0, 1, 3)
        self.gridLayout.addWidget(self.groupBox, 0, 2, 1, 1)
        self.TimesWorld = QtGui.QGroupBox(self.centralwidget)
        self.TimesWorld.setObjectName(_fromUtf8("TimesWorld"))
        self.gridLayout_5 = QtGui.QGridLayout(self.TimesWorld)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.txt_utc = QtGui.QLabel(self.TimesWorld)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Digital-7"))
        font.setPointSize(50)
        self.txt_utc.setFont(font)
        self.txt_utc.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_utc.setObjectName(_fromUtf8("txt_utc"))
        self.gridLayout_5.addWidget(self.txt_utc, 0, 0, 1, 1)
        self.txt_localtime = QtGui.QLabel(self.TimesWorld)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Digital-7"))
        font.setPointSize(50)
        self.txt_localtime.setFont(font)
        self.txt_localtime.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_localtime.setObjectName(_fromUtf8("txt_localtime"))
        self.gridLayout_5.addWidget(self.txt_localtime, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.TimesWorld, 1, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "SOFIA Science Cruise Director", None))
        self.groupBox_2.setTitle(_translate("MainWindow", "Logging", None))
        self.log_quick_takeoff.setText(_translate("MainWindow", "Takeoff", None))
        self.log_quick_onheading.setText(_translate("MainWindow", "On Heading", None))
        self.log_quick_ontarget.setText(_translate("MainWindow", "On Target", None))
        self.log_quick_turning.setText(_translate("MainWindow", "Turning", None))
        self.log_quick_faultmccs.setText(_translate("MainWindow", "MCCS Problem", None))
        self.log_quick_faultsi.setText(_translate("MainWindow", "SI Problem", None))
        self.log_quick_landing.setText(_translate("MainWindow", "Landing", None))
        self.log_save.setText(_translate("MainWindow", "Choose Output Filename", None))
        self.log_display.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.Lucida Grande UI\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.log_post.setText(_translate("MainWindow", "Post", None))
        self.txt_logoutputname.setText(_translate("MainWindow", "No Output Filename!", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.directorLogTab), _translate("MainWindow", "Cruise Director Log", None))
        self.datalog_savefile.setText(_translate("MainWindow", "Set Log Output File", None))
        self.datalog_opendir.setText(_translate("MainWindow", "Set Data Directory", None))
        self.datalog_autoupdate.setText(_translate("MainWindow", "Autoupdate every", None))
        self.datalog_updateinterval.setSuffix(_translate("MainWindow", " seconds", None))
        self.datalog_forceupdate.setText(_translate("MainWindow", "Force Update", None))
        self.datalog_forcewrite.setText(_translate("MainWindow", "Force Write", None))
        self.datalog_editFITSKeys.setText(_translate("MainWindow", "Edit FITS Keywords to Query...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.dataLogTab), _translate("MainWindow", "Data Log", None))
        self.LegTimers.setTitle(_translate("MainWindow", "Leg Timers", None))
        self.leg_timer_stop.setText(_translate("MainWindow", "Stop", None))
        self.leg_timer_reset.setText(_translate("MainWindow", "Reset", None))
        self.leg_timer_start.setText(_translate("MainWindow", "Start", None))
        self.time_select_remaining.setText(_translate("MainWindow", "Time Remaining", None))
        self.time_select_elapsed.setText(_translate("MainWindow", "Time Elapsed", None))
        self.leg_duration.setToolTip(_translate("MainWindow", "HH:MM:SS", None))
        self.leg_duration.setDisplayFormat(_translate("MainWindow", "hh:mm:ss", None))
        self.txt_leg_duration.setText(_translate("MainWindow", "Leg Duration", None))
        self.txt_leg_timer.setText(_translate("MainWindow", "+00:00:00", None))
        self.LegInformation.setTitle(_translate("MainWindow", "Flight Plan Information", None))
        self.leg_next.setText(_translate("MainWindow", "Next Leg", None))
        self.leg_next.setShortcut(_translate("MainWindow", ">, Ctrl+M", None))
        self.leg_previous.setText(_translate("MainWindow", "Previous Leg", None))
        self.leg_previous.setShortcut(_translate("MainWindow", "<, Ctrl+N", None))
        self.landing_time.setDisplayFormat(_translate("MainWindow", "MM/dd/yyyy HH:mm:ss", None))
        self.set_landingFP.setText(_translate("MainWindow", "Set Landing from Plan", None))
        self.set_takeoffFP.setText(_translate("MainWindow", "Set Takeoff from Plan", None))
        self.takeoff_time.setDisplayFormat(_translate("MainWindow", "MM/dd/yyyy HH:mm:ss", None))
        self.flightplan_filename.setText(_translate("MainWindow", "No Flight Plan Loaded!", None))
        self.flightplan_openfile.setText(_translate("MainWindow", "Open Flight Plan", None))
        self.flightplan_openfile.setShortcut(_translate("MainWindow", "Ctrl+O", None))
        self.txt_elevation.setText(_translate("MainWindow", "Elevation Range:", None))
        self.txt_leg.setText(_translate("MainWindow", "Leg:", None))
        self.txt_rof.setText(_translate("MainWindow", "ROF | ROFrate:", None))
        self.txt_obsplan.setText(_translate("MainWindow", "ObsPlan:", None))
        self.txt_target.setText(_translate("MainWindow", "Target:", None))
        self.groupBox.setTitle(_translate("MainWindow", "Current Flight Progress", None))
        self.set_takeoff_time.setText(_translate("MainWindow", "Start MET", None))
        self.set_landing_time.setText(_translate("MainWindow", "Start TTL", None))
        self.set_takeofflanding.setText(_translate("MainWindow", "Start Both", None))
        self.txt_ttl.setText(_translate("MainWindow", "TTL", None))
        self.txt_met.setText(_translate("MainWindow", "MET", None))
        self.TimesWorld.setTitle(_translate("MainWindow", "World Times", None))
        self.txt_utc.setText(_translate("MainWindow", "UTC", None))
        self.txt_localtime.setText(_translate("MainWindow", "LOCAL", None))


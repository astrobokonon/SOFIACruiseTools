# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 16:40:05 2015

@author: rhamilton
"""
# Started adapting from:
#  http://nikolak.com/pyqt-qt-designer-getting-started/


import os
import sys
import pytz
import datetime

import numpy as np
from PyQt4 import QtGui, QtCore

import fp_helper as fpmis
import SOFIACruiseDirectorPanel as scdp


class SOFIACruiseDirectorApp(QtGui.QMainWindow, scdp.Ui_MainWindow):
    def __init__(self):
        # Since the SOFIACruiseDirectorPanel file will be overwritten each time
        #   we change something in the design and recreate it, we will not be
        #   writing any code in it, instead we'll create a new class to
        #   combine with the design code
        super(self.__class__, self).__init__()
        # This is defined in SOFIACruiseDirectorPanel.py file automatically;
        #   It sets up layout and widgets that are defined
        self.setupUi(self)

        # Some constants/tracking variables and various defaults
        self.legpos = 0
        self.successparse = False
        self.toggle_legparam_values_off()
        self.metcounting = False
        self.ttlcounting = False
        self.legcounting = False
        self.legcountingstopped = False
        self.localtz = pytz.timezone('US/Pacific')
        self.setDateTimeEditBoxes()
        self.txt_met.setText("MET +00:00:00")
        self.txt_ttl.setText("TTL +00:00:00")

        # Hooking up the various buttons to their actions to take
        # Open the file chooser for the flight plan input
        self.flightplan_openfile.clicked.connect(self.selectFile)
        # Flight plan progression
        self.leg_previous.clicked.connect(self.prevLeg)
        self.leg_next.clicked.connect(self.nextLeg)
        # Start the flight progression timers
        self.set_takeoff_time.clicked.connect(self.settakeoff)
        self.set_landing_time.clicked.connect(self.setlanding)
        # Leg timer control
        self.leg_timer_start.clicked.connect(self.startlegtimer)
        self.leg_timer_stop.clicked.connect(self.stoplegtimer)
        self.leg_timer_reset.clicked.connect(self.resetlegtimer)

        # Generic timer setup stuff
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.showlcd)
        timer.start(500)
        self.showlcd()

    def startlegtimer(self):
        self.legcounting = True
        self.timerstarttime = datetime.datetime.now()
        self.timerstarttime = self.timerstarttime.replace(microsecond=0)
        if self.legcountingstopped is False:
            hms = self.leg_duration.time().toPyTime()
            dhour = hms.hour
            dmins = hms.minute
            dsecs = hms.second
        else:
            newdur = self.txt_leg_timer.text()
            dhour = np.int(newdur.split(":")[0])
            dmins = np.int(newdur.split(":")[1])
            dsecs = np.int(newdur.split(":")[2])

        durationDT = datetime.timedelta(hours=dhour,
                                        minutes=dmins,
                                        seconds=dsecs)
        self.timerendtime = self.timerstarttime + durationDT
        self.legcountingstopped = False

    def stoplegtimer(self):
        self.legcounting = False
        self.legcountingstopped = True

    def resetlegtimer(self):
        self.legcounting = True
        self.timerstarttime = datetime.datetime.now()
        self.timerstarttime = self.timerstarttime.replace(microsecond=0)
        hms = self.leg_duration.time().toPyTime()
        dhour = hms.hour
        dmins = hms.minute
        dsecs = hms.second
        durationDT = datetime.timedelta(hours=dhour,
                                        minutes=dmins,
                                        seconds=dsecs)
        self.timerendtime = self.timerstarttime + durationDT

    def totalsec_to_hms_str(self, obj):
        tsecs = obj.total_seconds()
        if tsecs < 0:
            isneg = True
            tsecs *= -1
        else:
            isneg = False
        hours = tsecs/60./60.
        ihrs = np.int(hours)
        minutes = (hours - ihrs)*60.
        imin = np.int(minutes)
        seconds = (minutes - imin)*60.
        if isneg is True:
            donestr = "-%02i:%02i:%02.0f" % (ihrs, imin, seconds)
        else:
            donestr = "+%02i:%02i:%02.0f" % (ihrs, imin, seconds)
        return donestr

    def setDateTimeEditBoxes(self):
        """
        Init. the takeoff and landing DateTimeEdit boxes to the time
        at the start of the app, so we don't have to type in as much.
        """
        # Get the current time(s)
        self.update_times()
        # Get the actual displayed formatting string (set in the UI file)
        self.takeoff_time.displayFormat()
        self.landing_time.displayFormat()
        # Make the current time into a QDateTime object that we can display
        cur = QtCore.QDateTime.fromString(self.localnow_datetimestr,
                                          self.takeoff_time.displayFormat())
        # Actually put it in the box
        self.takeoff_time.setDateTime(cur)
        self.landing_time.setDateTime(cur)

    def settakeoff(self):
        self.metcounting = True
        self.takeoff = self.takeoff_time.dateTime().toPyDateTime()
        # Add tzinfo to this object to make it able to interact
        self.takeoff = self.takeoff.replace(tzinfo=self.localtz)

    def setlanding(self):
        self.ttlcounting = True
        self.landing = self.landing_time.dateTime().toPyDateTime()
        # Add tzinfo to this object to make it able to interact
        self.landing = self.landing.replace(tzinfo=self.localtz)

    def update_times(self):
        """
        Grab the current UTC and local timezone time, and populate the strings.
        We need to throw away microseconds so everything will count together,
        otherwise it'll be out of sync due to microsecond delay between
        triggers/button presses.
        """
        self.utcnow = datetime.datetime.utcnow()
        self.utcnow = self.utcnow.replace(microsecond=0)
        self.utcnow_str = self.utcnow.strftime('%H:%M:%S UTC')
        self.utcnow_datetimestr = self.utcnow.strftime('%m/%d/%Y %H:%M:%S $Z')

        # Safest way to sensibly go from UTC -> local timezone...?
        self.localnow = self.utcnow.replace(
            tzinfo=pytz.utc).astimezone(self.localtz)
        self.localnow_str = self.localnow.strftime('%H:%M:%S %Z')
        self.localnow_datetimestr = self.localnow.strftime(
            '%m/%d/%Y %H:%M:%S')

    def showlcd(self):
        self.update_times()
        if self.metcounting is True:
            # We set the takeoff time to be in local time, and we know the
            #   current time is in local as well. So ditch the tzinfo because
            #   timezones suck and it's a big pain in the ass otherwise
            local2 = self.localnow.replace(tzinfo=None)
            takeoff2 = self.takeoff.replace(tzinfo=None)
            self.met = local2 - takeoff2
            self.metstr = "MET " + self.totalsec_to_hms_str(self.met)
            self.txt_met.setText(self.metstr)
        if self.ttlcounting is True:
            local2 = self.localnow.replace(tzinfo=None)
            landing2 = self.landing.replace(tzinfo=None)
            self.ttl = landing2 - local2
            self.ttlstr = "TTL " + self.totalsec_to_hms_str(self.ttl)
            self.txt_ttl.setText(self.ttlstr)
        if self.legcounting is True:
            local2 = self.localnow.replace(tzinfo=None)
            legend = self.timerendtime.replace(tzinfo=None)
            self.legremain = legend - local2
            self.legremainstr = self.totalsec_to_hms_str(self.legremain)
            self.txt_leg_timer.setText(self.legremainstr)

        self.txt_utc.setText(self.utcnow_str)
        self.txt_kpmd.setText(self.localnow_str)

    def toggle_legparam_labels_off(self):
        self.txt_elevation.setVisible(False)
        self.txt_obsplan.setVisible(False)
        self.txt_rof.setVisible(False)
        self.txt_target.setVisible(False)

    def toggle_legparam_values_off(self):
        self.leg_elevation.setText('')
        self.leg_obsblock.setText('')
        self.leg_rofrofrt.setText('')
        self.leg_target.setText('')

    def toggle_legparam_labels_on(self):
        self.txt_elevation.setVisible(True)
        self.txt_obsplan.setVisible(True)
        self.txt_rof.setVisible(True)
        self.txt_target.setVisible(True)

    def updateLegInfoWindow(self):
        self.leg_number.setText(str(self.legpos + 1))
        self.leg_target.setText(self.lginfo.target)

        if self.lginfo.legtype is 'Observing':
            self.toggle_legparam_labels_on()
            elevation_label = "%.1f to %.1f" % (self.lginfo.range_elev[0],
                                                self.lginfo.range_elev[1])
            self.leg_elevation.setText(elevation_label)
            rof_label = "%.1f to %.1f | %.1f to %.1f" % \
                (self.lginfo.range_rof[0], self.lginfo.range_rof[1],
                 self.lginfo.range_rofrt[0], self.lginfo.range_rofrt[1])
            self.leg_rofrofrt.setText(rof_label)
            self.leg_obsblock.setText(self.lginfo.obsplan)
        else:
            self.toggle_legparam_values_off()
            # Quick and dirty way to show the leg type
            legtxt = "%i %s" % (self.legpos + 1, self.lginfo.legtype)
            self.leg_number.setText(legtxt)

        # Now take the duration and autoset our timer duration
        timeparts = self.lginfo.duration.split(":")
        timeparts = [np.int(x) for x in timeparts]
        durtime = QtCore.QTime(timeparts[0], timeparts[1], timeparts[2])
        self.leg_duration.setTime(durtime)

    def prevLeg(self):
        if self.successparse is True:
            self.legpos -= 1
            if self.legpos < 0:
                self.legpos = 0
            self.lginfo = self.flightinfo.legs[self.legpos]
        self.updateLegInfoWindow()

    def nextLeg(self):
        if self.successparse is True:
            self.legpos += 1
            if self.legpos > self.flightinfo.nlegs-1:
                self.legpos = self.flightinfo.nlegs-1
            self.lginfo = self.flightinfo.legs[self.legpos]
        else:
            pass
        self.updateLegInfoWindow()

    def updateTakeoffTime(self):
        fptakeoffDT = self.flightinfo.takeoff.replace(tzinfo=pytz.utc)
        fptakeoffDT = fptakeoffDT.astimezone(self.localtz)
        fptakeoffstr = fptakeoffDT.strftime("%m/%d/%Y %H:%M:%S")
        fptakeoffQt = QtCore.QDateTime.fromString(fptakeoffstr,
                                                  "MM/dd/yyyy HH:mm:ss")
        self.takeoff_time.setDateTime(fptakeoffQt)

    def updateLandingTime(self):
        fplandingDT = self.flightinfo.landing.replace(tzinfo=pytz.utc)
        fplandingDT = fplandingDT.astimezone(self.localtz)
        fplandingstr = fplandingDT.strftime("%m/%d/%Y %H:%M:%S")
        fplandingQt = QtCore.QDateTime.fromString(fplandingstr,
                                                  "MM/dd/yyyy HH:mm:ss")
        self.landing_time.setDateTime(fplandingQt)

    def selectFile(self):
        self.fname = QtGui.QFileDialog.getOpenFileName()
        self.flightplan_filename.setStyleSheet("QLabel { color : black; }")
        self.flightplan_filename.setText(os.path.basename(self.fname))
        try:
            self.flightinfo = fpmis.parse_fpmis(self.fname)
            self.lginfo = self.flightinfo.legs[self.legpos]
            self.successparse = True
            self.updateLegInfoWindow()
            if self.set_takeoffFP.isChecked() is True:
                self.updateTakeoffTime()
            if self.set_landingFP.isChecked() is True:
                self.updateLandingTime()
        except Exception:
            self.flightinfo = ''
            self.errmsg = 'ERROR: Failure Parsing File!'
            self.flightplan_filename.setStyleSheet("QLabel { color : red; }")
            self.flightplan_filename.setText(self.errmsg)
            self.successparse = False

    def browse_folder(self):
        # In case there are any existing elements in the list
        self.listWidget.clear()
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                                           "Pick a folder")
        # execute getExistingDirectory dialog and set the directory
        #   variable to be equal to the user selected directory

        # if user didn't pick a directory don't continue
        if directory:
            # for all files, if any, in the directory
            for file_name in os.listdir(directory):
                # add file to the listWidget
                self.listWidget.addItem(file_name)


def main():
    app = QtGui.QApplication(sys.argv)
    form = SOFIACruiseDirectorApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()

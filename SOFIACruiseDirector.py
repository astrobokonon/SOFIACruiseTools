# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 16:40:05 2015

@author: rhamilton
"""
# Regen the UI Py file via:
#   pyuic4-2.7 SOFIACruiseDirectorPanel.ui -o SOFIACruiseDirectorPanel.py

# Current bug:
#  If you put the output file in the wrong place and try to redefine it,
#  screwy things result and either the name updates underneath of you
#  or it doesn't actually write to the new location?


import os
import sys
import csv
import pytz
import glob
import datetime

import numpy as np
#import astropy.io.fits as pyf
import pyfits as pyf
from PyQt4 import QtGui, QtCore

import fp_helper as fpmis
import SOFIACruiseDirectorPanel as scdp


def grab_header(infile, headerlist, HDU=0):
    """
    Given a FITS file and a list of header keywords of interest,
    parse those two together and return the result.
    """
    key = ''
    bname = os.path.basename(infile)
    # NOW NEED TO ADD IN GRABBING THE RIGHT HDU
    try:
        hed = pyf.getheader(infile)
    except:
        hed = ' '

    item = []
    for key in headerlist:
        try:
            item.append(hed[key])
        except:
            item.append('')

    return bname, item


def grab_headers(inlist, headerlist):
    """
    Given a list of FITS files and a list of header keywords of interest,
    parse those two together and return the result.
    """
    ret = []
    key = ''
    for each in inlist:
        bname = os.path.basename(each)
        try:
            hed = pyf.getheader(each)
            item = []
            for key in headerlist:
                try:
                    item.append(hed[key])
                except:
                    item.append('')
            ret.append([bname, item])
        except:
            pass
    return ret


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
        self.doLegCountRemaining = True
        self.doLegCountElapsed = False
        self.outputname = ''
        self.localtz = pytz.timezone('US/Pacific')
        self.setDateTimeEditBoxes()
        self.txt_met.setText("+00:00:00 MET")
        self.txt_ttl.setText("+00:00:00 TTL")
        # Is a list really the best way of handling this? Don't know yet.
        self.CruiseLog = []
        self.startdatalog = False
        self.data_current = []
        self.data_previous = []
        self.datatable = []
        self.datafilenames = []
        self.logoutputname = ''
        self.headers = []

        self.updateheadlist()
#        self.headers = ['itime', 'co_adds', 'object', 'sibs_x', 'sibs_y',
#                        'telra', 'teldec', 'telel', 'tellos', 'alti_sta',
#                        'spectel1', 'slit', 'planid', 'aor_id',
#                        'instmode', 'instcfg', 'obstype', 'nodbeam']
        self.headers = [hlab.upper() for hlab in self.headers]

        # Notes position is first in the table
        self.table_datalog.insertColumn(0)

        # Add the number of columns we'll need for the header keys given
        for hkey in self.headers:
            colPosition = self.table_datalog.columnCount()
            self.table_datalog.insertColumn(colPosition)

        # This always puts the NOTES col. right next to the filename
        self.table_datalog.setHorizontalHeaderLabels(['NOTES'] + self.headers)
        # This always puts the NOTES col. at the end of all the other cols.
#        self.table_datalog.setHorizontalHeaderLabels(self.headers + ['NOTES'])

        self.table_datalog.resizeColumnsToContents()
        self.table_datalog.resizeRowsToContents()
        self.table_datalog.show()

        # Hooking up the various buttons to their actions to take
        # Open the file chooser for the flight plan input
        self.flightplan_openfile.clicked.connect(self.selectInputFile)
        # Flight plan progression
        self.leg_previous.clicked.connect(self.prevLeg)
        self.leg_next.clicked.connect(self.nextLeg)
        # Start the flight progression timers
        self.set_takeoff_time.clicked.connect(self.settakeoff)
        self.set_landing_time.clicked.connect(self.setlanding)
        self.set_takeofflanding.clicked.connect(self.settakeoffandlanding)
        # Leg timer control
        self.leg_timer_start.clicked.connect(self.startlegtimer)
        self.leg_timer_stop.clicked.connect(self.stoplegtimer)
        self.leg_timer_reset.clicked.connect(self.resetlegtimer)
        # Leg timer counting type (radio buttons)
        self.time_select_remaining.clicked.connect(self.countremaining)
        self.time_select_elapsed.clicked.connect(self.countelapsed)
        # Text log stuff
        self.log_post.clicked.connect(self.postlogline)
        self.log_inputline.returnPressed.connect(self.postlogline)

        self.log_quick_faultmccs.clicked.connect(self.mark_faultmccs)
        self.log_quick_faultsi.clicked.connect(self.mark_faultsi)
        self.log_quick_landing.clicked.connect(self.mark_landing)
        self.log_quick_onheading.clicked.connect(self.mark_onheading)
        self.log_quick_ontarget.clicked.connect(self.mark_ontarget)
        self.log_quick_takeoff.clicked.connect(self.mark_takeoff)
        self.log_quick_turning.clicked.connect(self.mark_turning)
        self.log_save.clicked.connect(self.selectOutputFile)
        self.datalog_opendir.clicked.connect(self.selectDir)
        self.datalog_savefile.clicked.connect(self.selectLogOutputFile)
        self.datalog_forcewrite.clicked.connect(self.writedatalog)
        self.datalog_forceupdate.clicked.connect(self.updateDatalog)

        # Generic timer setup stuff
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.showlcd)
        timer.start(500)
        self.showlcd()

    def updateheadlist(self):
        for j in range(self.fitskw_listing.count()):
            ched = self.fitskw_listing.item(j).text()
            self.headers.append(ched)

    def selectDir(self):
        dtxt = 'Select Data Directory'
        self.datalogdir = QtGui.QFileDialog.getExistingDirectory(self, dtxt)
        self.txt_datalogdir.setText(self.datalogdir)
        self.startdatalog = True

    def linestamper(self, line):
        timestamp = datetime.datetime.utcnow()
        timestamp = timestamp.replace(microsecond=0)
        stampedline = timestamp.isoformat() + "> " + line
        self.CruiseLog.append(stampedline + '\n')
        self.log_display.append(stampedline)
        if self.outputname != '':
            try:
                f = open(self.outputname, 'w')
                f.writelines(self.CruiseLog)
                f.close()
            except Exception:
                self.txt_logoutputname.setText("ERROR WRITING TO FILE!")

    def mark_faultmccs(self):
        line = "MCCS fault encountered"
        self.linestamper(line)

    def mark_faultsi(self):
        line = "SI fault encountered"
        self.linestamper(line)

    def mark_landing(self):
        line = "End of flight, packing up and sitting down"
        self.linestamper(line)

    def mark_onheading(self):
        line = "On heading, TOs setting up"
        self.linestamper(line)

    def mark_ontarget(self):
        line = "On target, SI taking over"
        self.linestamper(line)

    def mark_takeoff(self):
        line = "Beginning of flight, getting set up"
        self.linestamper(line)

    def mark_turning(self):
        line = "Turning off target"
        self.linestamper(line)

    def selectOutputFile(self):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to both open and write to the file.

        """
        defaultname = "SILog_" + self.utcnow.strftime("%Y%m%d.txt")
        self.outputname = QtGui.QFileDialog.getSaveFileName(self, "Save File",
                                                            defaultname)
        self.txt_logoutputname.setText("Writing to: " +
                                       os.path.basename(str(self.outputname)))

    def selectLogOutputFile(self):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to both open and write to the file.

        """
        defaultname = "DataLog_" + self.utcnow.strftime("%Y%m%d.txt")
        self.logoutputname = QtGui.QFileDialog.getSaveFileName(self,
                                                               "Save File",
                                                               defaultname)
        self.txt_datalogsavefile.setText("Writing to: " +
                                         os.path.basename(str(self.logoutputname)))

    def postlogline(self):
        line = self.log_inputline.text()
        self.linestamper(line)
        # Clear the line
        self.log_inputline.setText('')

    def countremaining(self):
        self.doLegCountElapsed = False
        self.doLegCountRemaining = True

    def countelapsed(self):
        self.doLegCountElapsed = True
        self.doLegCountRemaining = False

    def startlegtimer(self):
        if self.legcounting is True:
            pass
        else:
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

    def settakeoffandlanding(self):
        self.settakeoff()
        self.setlanding()

    def update_times(self):
        """
        Grab the current UTC and local timezone time, and populate the strings.
        We need to throw away microseconds so everything will count together,
        otherwise it'll be out of sync due to microsecond delay between
        triggers/button presses.
        """
        self.utcnow = datetime.datetime.utcnow()
        self.utcnow = self.utcnow.replace(microsecond=0)
        self.utcnow_str = self.utcnow.strftime(' %H:%M:%S UTC')
        self.utcnow_datetimestr = self.utcnow.strftime('%m/%d/%Y %H:%M:%S $Z')

        # Safest way to sensibly go from UTC -> local timezone...?
        self.localnow = self.utcnow.replace(
            tzinfo=pytz.utc).astimezone(self.localtz)
        self.localnow_str = self.localnow.strftime(' %H:%M:%S %Z')
        self.localnow_datetimestr = self.localnow.strftime(
            '%m/%d/%Y %H:%M:%S')

    def showlcd(self):
        """
        Contains the clock logic code for all the various timers.

        MET: Mission Elapsed Time
        TTL: Time unTill Landing
        Plus the leg timer variants (elapsed/remaining)

        Since the times were converted to local elsewhere,
        we ditch the tzinfo to make everything naive to subtract easier.
        """
        # Update the current local/utc times before computing timedeltas
        self.update_times()
        # We set the takeoff time to be in local time, and we know the
        #   current time is in local as well. So ditch the tzinfo because
        #   timezones suck and it's a big pain in the ass otherwise.
        #   The logic follows the same for each counter/timer.
        if self.metcounting is True:
            local2 = self.localnow.replace(tzinfo=None)
            takeoff2 = self.takeoff.replace(tzinfo=None)
            self.met = local2 - takeoff2
            self.metstr = self.totalsec_to_hms_str(self.met) + " MET"
            self.txt_met.setText(self.metstr)
        if self.ttlcounting is True:
            local2 = self.localnow.replace(tzinfo=None)
            landing2 = self.landing.replace(tzinfo=None)
            self.ttl = landing2 - local2
            self.ttlstr = self.totalsec_to_hms_str(self.ttl) + " TTL"
            self.txt_ttl.setText(self.ttlstr)

            # Visual indicators setup
            if self.ttl.total_seconds() >= 7200:
                self.txt_ttl.setStyleSheet("QLabel { color : black; }")

            elif self.ttl.total_seconds() < 7200 and\
                    self.ttl.total_seconds() >= 5400:
                self.txt_ttl.setStyleSheet("QLabel { color : yellow; }")

            elif self.ttl.total_seconds() < 5400:
                self.txt_ttl.setStyleSheet("QLabel { color : red; }")

        if self.legcounting is True:
            local2 = self.localnow.replace(tzinfo=None)
            legend = self.timerendtime.replace(tzinfo=None)
            legstart = self.timerstarttime.replace(tzinfo=None)

            if self.doLegCountRemaining is True:
                self.legremain = legend - local2
                self.legremainstr = self.totalsec_to_hms_str(self.legremain)
                self.txt_leg_timer.setText(self.legremainstr)

                # Visual indicators setup
                if self.legremain.total_seconds() >= 3600:
                    self.txt_leg_timer.setStyleSheet(
                        "QLabel { color : black; }")

                elif self.legremain.total_seconds() < 3600 and\
                        self.legremain.total_seconds() >= 2400:
                    self.txt_leg_timer.setStyleSheet(
                        "QLabel { color : yellow; }")

                elif self.legremain.total_seconds() < 2400:
                    self.txt_leg_timer.setStyleSheet("QLabel { color : red; }")

            if self.doLegCountElapsed is True:
                self.legelapsed = local2 - legstart
                self.legelapsedstr = self.totalsec_to_hms_str(self.legelapsed)
                self.txt_leg_timer.setText(self.legelapsedstr)

        self.txt_utc.setText(self.utcnow_str)
        self.txt_localtime.setText(self.localnow_str)

        if self.startdatalog is True and\
           self.datalog_autoupdate.isChecked() is True:
            if self.utcnow.second % self.datalog_updateinterval.value() == 0:
                self.updateDatalog()
#                print self.datatable

    def updateDatalog(self):
        # Get the current list of FITS files in the location
        self.data_current = glob.glob(str(self.datalogdir) + "/*.fits")
        # If the length of the current listing is bigger than
        #   the previous, then lets look at the new files.
        #   This avoids the situation where files disappear
        #   and cause off-by-one errors that we don't want to deal with
        #   in this first early version.
        if len(self.data_current) > len(self.data_previous):
            self.datanew = []
            # Make the unique listing of old files
            s = set(self.data_previous)
            # Compare the new listing to the unique set of the old ones
            diff = [x for x in self.data_current if x not in s]
            # Capture the last row position so we know where to start
            self.lastdatarow = self.table_datalog.rowCount()
            # Actually query the files for the desired headers
            for newfile in diff:
                # Save the filenames
                self.datafilenames.append(os.path.basename(newfile))
                # Add number of rows for files to go into first
                rowPosition = self.table_datalog.rowCount()
                self.table_datalog.insertRow(rowPosition)
                # Actually get the header data
                # NEED TO ADD ADDITIONAL HDU ARGUMENT RIGHT HERE
                self.datanew.append(grab_header(newfile,
                                                self.headers),
                                                HDU=self.fitskw_currenthdu.value())

            self.setTableData()
            self.writedatalog()

        self.data_previous = self.data_current

    def setTableData(self):
        if len(self.datanew[0]) != 0:

            # Disable fun stuff while we update
            self.table_datalog.setSortingEnabled(False)
            self.table_datalog.horizontalHeader().setMovable(False)
            self.table_datalog.horizontalHeader().setDragEnabled(False)
            self.table_datalog.horizontalHeader().setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)

            # Actually set the labels for rows
            self.table_datalog.setVerticalHeaderLabels(self.datafilenames)
            # Create the data table items and populate things

            for n, row in enumerate(self.datanew):
                for m, col in enumerate(row[1]):
                    newitem = QtGui.QTableWidgetItem(str(col))
                    self.table_datalog.setItem(n + self.lastdatarow,
                                               m+1, newitem)

            # Resize to minimum required, then display
#            self.table_datalog.resizeColumnsToContents()
            self.table_datalog.resizeRowsToContents()

            # Seems to be more trouble than it's worth, so keep this commented
#            self.table_datalog.setSortingEnabled(True)

            # Reenable fun stuff
            self.table_datalog.horizontalHeader().setMovable(True)
            self.table_datalog.horizontalHeader().setDragEnabled(True)
            self.table_datalog.horizontalHeader().setDragDropMode(QtGui.QAbstractItemView.InternalMove)
#            self.table_datalog.setDragEnabled(True)
#            self.table_datalog.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

            self.table_datalog.show()

    def writedatalog(self):
        if self.logoutputname != '':
            try:
                f = open(self.logoutputname, 'w')
                writer = csv.writer(f)
                for row in range(self.table_datalog.rowCount()):
                    rowdata = []
                    rowdata.append(self.datafilenames[row])
                    for column in range(self.table_datalog.columnCount()):
                        item = self.table_datalog.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)
                f.close()
            except Exception, why:
                print str(why)
                self.txt_datalogsavefile.setText("ERROR WRITING TO FILE!")

    def toggle_legparam_labels_off(self):
        """
        Quick method to hide the leg parameter labels,
        should we find them distracting
        """
        self.txt_elevation.setVisible(False)
        self.txt_obsplan.setVisible(False)
        self.txt_rof.setVisible(False)
        self.txt_target.setVisible(False)

    def toggle_legparam_values_off(self):
        """
        Quick method to clear the leg parameter values,
        should we know them to be wrong/bogus
        (such as on dead/departure/arrival) legs
        """
        self.leg_elevation.setText('')
        self.leg_obsblock.setText('')
        self.leg_rofrofrt.setText('')
        self.leg_target.setText('')

    def toggle_legparam_labels_on(self):
        """
        Quick method to ensure that the leg parameter labels are visible
        """
        self.txt_elevation.setVisible(True)
        self.txt_obsplan.setVisible(True)
        self.txt_rof.setVisible(True)
        self.txt_target.setVisible(True)

    def updateLegInfoWindow(self):
        """
        If the flight plan was successfully parsed, show the values
        for the leg occuring at self.legpos (+1 if you prefer 1-indexed)
        """
        # Only worth doing if we read in a flight plan file
        if self.successparse is True:
            # Quick and dirty way to show the leg type
            legtxt = "%i\t%s" % (self.legpos + 1, self.lginfo.legtype)
            self.leg_number.setText(legtxt)

            # Target name
            self.leg_target.setText(self.lginfo.target)

            # If the leg type is an observing leg, show the deets
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
                # If it's a dead leg, update the leg number and we'll move on
                # Clear values since they're probably crap
                self.toggle_legparam_values_off()
                # Quick and dirty way to show the leg type
                legtxt = "%i\t%s" % (self.legpos + 1, self.lginfo.legtype)
                self.leg_number.setText(legtxt)

            # Now take the duration and autoset our timer duration
            timeparts = self.lginfo.duration.split(":")
            timeparts = [np.int(x) for x in timeparts]
            durtime = QtCore.QTime(timeparts[0], timeparts[1], timeparts[2])
            self.leg_duration.setTime(durtime)

    def prevLeg(self):
        """
        Move the leg position counter to the previous value,
        bottoming out at 0
        """
        if self.successparse is True:
            self.legpos -= 1
            if self.legpos < 0:
                self.legpos = 0
            self.lginfo = self.flightinfo.legs[self.legpos]
        self.updateLegInfoWindow()

    def nextLeg(self):
        """
        Move the leg position counter to the next value,
        hitting the ceiling at the max number of found legs
        """
        if self.successparse is True:
            self.legpos += 1
            if self.legpos > self.flightinfo.nlegs-1:
                self.legpos = self.flightinfo.nlegs-1
            self.lginfo = self.flightinfo.legs[self.legpos]
        else:
            pass
        self.updateLegInfoWindow()

    def updateTakeoffTime(self):
        """
        Grab the flight takeoff time from the flight plan, which is in UTC,
        and turn it into the time at the local location.

        Then, take that time and update the DateTimeEdit box in the GUI
        """
        fptakeoffDT = self.flightinfo.takeoff.replace(tzinfo=pytz.utc)
        fptakeoffDT = fptakeoffDT.astimezone(self.localtz)
        fptakeoffstr = fptakeoffDT.strftime("%m/%d/%Y %H:%M:%S")
        fptakeoffQt = QtCore.QDateTime.fromString(fptakeoffstr,
                                                  "MM/dd/yyyy HH:mm:ss")
        self.takeoff_time.setDateTime(fptakeoffQt)

    def updateLandingTime(self):
        """
        Grab the flight landing time from the flight plan, which is in UTC,
        and turn it into the time at the local location.

        Then, take that time and update the DateTimeEdit box in the GUI
        """
        fplandingDT = self.flightinfo.landing.replace(tzinfo=pytz.utc)
        fplandingDT = fplandingDT.astimezone(self.localtz)
        fplandingstr = fplandingDT.strftime("%m/%d/%Y %H:%M:%S")
        fplandingQt = QtCore.QDateTime.fromString(fplandingstr,
                                                  "MM/dd/yyyy HH:mm:ss")
        self.landing_time.setDateTime(fplandingQt)

    def selectInputFile(self):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).

        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance
        """
        self.fname = QtGui.QFileDialog.getOpenFileName()
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
        self.flightplan_filename.setStyleSheet("QLabel { color : black; }")
        self.flightplan_filename.setText(os.path.basename(str(self.fname)))
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
        titlestr = "Choose a SOFIA mission file (.mis)"
        directory = QtGui.QFileDialog.getExistingDirectory(self, titlestr)

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

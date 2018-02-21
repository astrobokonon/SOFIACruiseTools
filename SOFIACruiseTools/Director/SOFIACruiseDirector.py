# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 16:40:05 2015

@author: rhamilton

Program to facilitate the logging of an observing run with SOFIA. 
Reads in a flight plan, parses out the legs of observations and targets.
Displays relevant timers for flight/leg.
Generates log files.

Program is structured around two objects:
  - SOFIACruiseDirectorApp: Main panel for the UI; everthing is based
    around this
  - FITSKeyWordDialog: Secondary panel allowing for interactive selection
    of header keywords to use. Currently does nothing.

Initialization of SOFIACruiseDirectorApp starts up the UI and begins the main
loop, a function called showlcd connected to a QtTimer object. 

"""
# Regen the UI Py file via:
#   pyuicX SOFIACruiseDirectorPanel.ui -o SOFIACruiseDirectorPanel.py
# Where X = your Qt version

# Trying to ensure Python 2/3 coexistance ...
from __future__ import division, print_function, absolute_import

import sys
import csv
import pytz
import glob
import fnmatch
import datetime
import itertools
from os import listdir, walk
from os.path import join, basename, getmtime
from collections import OrderedDict

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

try:
    import astropy.io.fits as pyf
except ImportError:
    import pyfits as pyf

from .. import support as fpmis
from . import FITSKeywordPanel as fkwp
from . import SOFIACruiseDirectorPanel as scdp


class SOFIACruiseDirectorApp(QtWidgets.QMainWindow, scdp.Ui_MainWindow):
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
        self.leg_pos = 0
        self.success_parse = False
        self.toggle_leg_param_values_off()
        # self.leg_param_labels('off')
        self.met_counting = False
        self.ttl_counting = False
        self.leg_counting = False
        self.leg_counting_stopped = False
        self.do_leg_count_remaining = True
        self.do_leg_count_elapsed = False
        self.output_name = ''
        self.localtz = pytz.timezone('US/Pacific')
        self.set_date_time_edit_boxes()
        self.txt_met.setText('+00:00:00 MET')
        self.txt_ttl.setText('+00:00:00 TTL')
        self.data = FITSHeader()

        # Is a list really the best way of handling this? Don't know yet.
        self.cruise_log = []
        self.start_data_log = False
        self.data_current = []
        self.data_previous = []
        self.data_table = []
        self.data_filenames = []
        self.log_out_name = ''
        self.headers = []
        self.fits_hdu = 0

        # Set the default instrument and FITS headers
        self.last_instrument_index = -1
        self.select_instr(0)
        # Things are easier if the keywords are always in CAPS
        self.headers = [each.upper() for each in self.headers]
        # The addition of the NOTES column happens in here
        self.update_table_cols()

        # Variables previously defined in function
        self.data_log_dir = ''
        self.timer_start_time = None
        self.timer_end_time = None
        self.takeoff = None
        self.landing = None
        self.utc_now = None
        self.utc_now_str = None
        self.utc_now_datetime_str = None
        self.local_now = None
        self.local_now_str = None
        self.local_now_datetime_str = None
        self.met = None
        self.met_str = None
        self.ttl = None
        self.ttl_str = None
        self.instrument = ''
        self.leg_remain = None
        self.leg_remain_str = None
        self.leg_elapsed = None
        self.leg_elapsed_str = None
        self.new_files = None
        self.data_new = None
        self.last_data_row = None
        self.leg_info = None
        self.fname = None
        self.err_msg = None
        self.kwname = None
        self.new_headers = None

        # Looks prettier with this stuff
        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()

        # Actually show the table
        self.table_data_log.show()

        ####
        # Set up buttons
        ####

        # Open the file chooser for the flight plan input
        self.flight_plan_openfile.clicked.connect(self.select_input_file)
        # Flight plan progression
        self.leg_previous.clicked.connect(self.prev_leg)
        self.leg_next.clicked.connect(self.next_leg)
        # Start the flight progression timers
        self.set_takeoff_time.clicked.connect(lambda: self.flight_timer('met'))
        self.set_landing_time.clicked.connect(lambda: self.flight_timer('ttl'))
        self.set_takeoff_landing.clicked.connect(lambda:
                                                 self.flight_timer('both'))
        # Leg timer control
        self.leg_timer_start.clicked.connect(lambda: self.leg_timer('start'))
        self.leg_timer_stop.clicked.connect(lambda: self.leg_timer('stop'))
        self.leg_timer_reset.clicked.connect(lambda: self.leg_timer('reset'))
        self.time_select_remaining.clicked.connect(lambda:
                                                   self.count_direction('remain'))
        self.time_select_elapsed.clicked.connect(lambda:
                                                 self.count_direction('elapse'))
        # Text log stuff
        self.log_input_line.returnPressed.connect(self.post_log_line)
        self.log_save.clicked.connect(self.select_output_file)

        self.log_fault_mccs.clicked.connect(lambda: self.mark_message('mccs'))
        self.log_fault_si.clicked.connect(lambda: self.mark_message('si'))
        self.log_landing.clicked.connect(lambda: self.mark_message('land'))
        self.log_on_heading.clicked.connect(lambda: self.mark_message('head'))
        self.log_on_target.clicked.connect(lambda: self.mark_message('target'))
        self.log_takeoff.clicked.connect(lambda: self.mark_message('takeoff'))
        self.log_turning.clicked.connect(lambda: self.mark_message('turn'))
        self.log_post.clicked.connect(lambda: self.mark_message('post'))

        self.data_log_open_dir.clicked.connect(self.select_dir)
        self.data_log_save_file.clicked.connect(self.select_log_output_file)
        self.data_log_force_write.clicked.connect(lambda: self.data.write_to_file(
                                                  self.log_out_name,
                                                  self.headers))
        self.data_log_force_update.clicked.connect(self.update_data_log)
        self.data_log_edit_keywords.clicked.connect(self.spawn_kw_window)
        self.data_log_add_row.clicked.connect(self.add_data_log_row)
        self.data_log_delete_row.clicked.connect(self.del_data_log_row)

        # Instrument selection
        self.data_log_instrument_select.activated.connect(self.select_instr)
        # Add an action that detects when a cell is changed by the user
        #  in table_datalog!

        # Generic timer setup stuff
        timer = QtCore.QTimer(self)
        # Set up the time to run self.showlcd() every 500 ms
        timer.timeout.connect(self.show_lcd)
        timer.start(500)
        self.show_lcd()

    def select_instr(self, index):
        """
        Sets the instrument and default FITS headers

        Controlled by the instrument selector on the data log tab. 
        When a new instrument is selected, the current instrument is
        changed to it, default headers are selected, and the data log 
        table is remade. This deletes the current data log table, so
        a dialog box is presented to warn the user and ensure they want 
        to proceed with changing the instrument.
        """

        # Check to see if the selection is a different instrument
        if index == self.last_instrument_index:
            return
        text = self.data_log_instrument_select.itemText(index)

        # Check if the table is populated
        if self.table_data_log.rowCount() > 0:
            # Changing headers clears the table, inform user
            choice = QtWidgets.QMessageBox.question(self, 'Warning',
                                                    'Warning!\n'
                                                    'Changing the instrument '
                                                    'will clear the log!\n'
                                                    'Continue?',
                                                    QtWidgets.QMessageBox.Yes |
                                                    QtWidgets.QMessageBox.No)
            # If the user says to not continue thus keeping the data log,   
            # reset the selector to the current instrument
            if choice == QtWidgets.QMessageBox.No:
                self.data_log_instrument_select.setCurrentIndex(
                    self.last_instrument_index)
                # num_items = self.data_log_instrument_select.count()
                return

        # Set the current instrument name and last_instrument_index
        if 'HAWC' in text:
            # Use HAWCFlight to support current SI file storage method
            self.instrument = 'HAWCFlight'
            key = 'hawc'
        else:
            self.instrument = text
            key = text.lower()
        self.last_instrument_index = index

        # Default headers for each instrument
        flitecam_headers = ['object', 'aor_id', 'exptime', 'itime', 'co_adds',
                            'spectel1', 'spectel2', 'fcfilta', 'fcfiltb',
                            'date-obs', 'time_gps', 'sibs_x', 'sibs_y', 'nodcrsys',
                            'nodangle', 'nodamp', 'nodbeam', 'dthpatt', 'dthnpos',
                            'dthindex', 'dthxoff', 'dthyoff', 'dthoffs',
                            'dthcrsys', 'telra', 'teldec', 'tellos', 'telrof',
                            'telvpa', 'BBMODE', 'CBMODE', 'BGRESETS', 'GRSTCNT',
                            'missn-id', 'instcfg', 'instmode']
        great_headers = list(flitecam_headers)
        exes_headers = list(flitecam_headers)
        hawc_headers = ['date-obs', 'object', 'mccsmode',
                        'spectel1', 'spectel2',
                        'instcfg', 'instmode', 'obsmode', 'scnpatt',
                        'calmode', 'exptime', 'nodtime', 'fcstoff',
                        'chpamp1', 'chpamp2', 'chpfreq',
                        'chpangle', 'chpcrsys', 'nodangle', 'nodcrsys',
                        'aor_id', 'dthindex', 'dthnpos',
                        'dthxoff', 'dthyoff', 'dthscale', 'dthunit',
                        'dthcrsys', 'scnrate', 'scncrsys', 'scniters',
                        'scnanglc', 'scnampel', 'scnampxl', 'scnfqrat',
                        'scnphase', 'scntoff', 'scnnsubs', 'scnlen',
                        'scnstep', 'scnsteps', 'scncross',
                        'intcalv', 'diag_hz',
                        'nhwp', 'hwpstart',
                        'telra', 'teldec', 'telvpa',
                        'obsra', 'obsdec', 'objra', 'objdec',
                        'za_start', 'za_end', 'focus_st', 'focus_en',
                        'utcstart', 'utcend',
                        'missn-id']
        fifi_headers = ['DATE-OBS', 'AOR_ID', 'OBJECT', 'EXPTIME',
                        'OBSRA', 'OBSDEC', 'DETCHAN', 'DICHROIC',
                        'ALTI_STA', 'ZA_START', 'NODSTYLE', 'NODBEAM',
                        'DLAM_MAP', 'DBET_MAP', 'DET_ANGL',
                        'OBSLAM', 'OBSBET', 'G_WAVE_B', 'G_WAVE_R']

        # Build a dictionary of default headers for each instrument
        headers = {'flitecam': flitecam_headers, 'great': great_headers,
                   'exes': exes_headers, 'hawc': hawc_headers,
                   'fifi-ls': fifi_headers, 'forcast': flitecam_headers}
        self.headers = ['NOTES']+headers[key]

        # Update the data_log headers
        # Things are easier if the keywords are always in CAPS
        self.headers = [each.upper() for each in self.headers]

        # The addition of the NOTES column happens in here
        # Remake the data log table
        self.update_table_cols()
        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()

    def spawn_kw_window(self):
        """
        Opens the FITS Keywords select window.

        Called when the 'Edit Keywords...' button on the Data Log tab
        is pressed. Currently does not affect anything.
        """
        window = FITSKeyWordDialog(self)
        # Open the FITS keyword dialog. The result is one if
        # the window is closed by pushing the okay button and
        # zero if the window is closed by pushing the 
        # cancel button. 
        result = window.exec_()
        if result == 1:
            self.fits_hdu = np.int(window.fitskw_hdu.value())
            self.new_headers = window.headers
            if 'NOTES' not in self.new_headers:
                self.new_headers.insert(0, 'NOTES')

            # Update the column data itself if we're actually logging
            if self.start_data_log is True:
                self.repopulate_data_log(rescan=False)

    def update_table_cols(self):
        """
        Updates the columns in the QTable Widget in the Data Log tab.

        Called initially when the window is first opened and again if the
        FITS keywords are changed via the repopulateDatalog function in  
        spamkwwindow function.
        Sets:
            table_data_log
        """

        # Get the size of the current table
        # cols = self.table_data_log.columnCount()
        # rows = self.table_data_log.rowCount()

        # Clear the table
        self.table_data_log.setColumnCount(0)
        self.table_data_log.setRowCount(0)

        # This always puts the NOTES col. right next to the filename
        # self.table_data_log.insertColumn(0)

        # Add the number of columns we'll need for the header keys given
        for hkey in self.headers:
            col_position = self.table_data_log.columnCount()
            self.table_data_log.insertColumn(col_position)
        # self.table_data_log.setHorizontalHeaderLabels(['NOTES'] + self.headers)
        self.table_data_log.setHorizontalHeaderLabels(self.headers)

    def select_dir(self):
        """
        Sets the location where data is stored.
    
        Opens a window to allow the user to select the directory 
        where data is being stored. Called when the 'Set Data Directory' 
        button on the Data Log tab is pressed.
        Sets:
            txt_datalogdir
            startdatalog
        """
        dtxt = 'Select Data Directory'
        self.data_log_dir = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       dtxt)
        if self.data_log_dir != '':
            self.txt_data_log_dir.setText(self.data_log_dir)
            self.start_data_log = True

    def line_stamper(self, line):
        """
        Updates the Cruise Director Log

        Called by:
            mark_fault_mccs, mark_fault_si, mark_landing,  
            mark_on_heading, mark_on_target, mark_takeoff,
            mark_turning, postlogline
        """
        # Format log line
        time_stamp = datetime.datetime.utcnow()
        time_stamp = time_stamp.replace(microsecond=0)
        stamped_line = '{0:s}> {1:s}'.format(time_stamp.isoformat(), line)
        # Write the log line to the cruise_log and log_display
        # cruise_log is a list
        # log_display is a QtWidgets.QTextEdit object
        self.cruise_log.append(stamped_line + '\n')
        self.log_display.append(stamped_line)

        if self.output_name != '':
            try:
                with open(self.output_name, 'w') as f:
                    f.writelines(self.cruise_log)
            except IOError:
                self.txt_log_output_name.setText('ERROR WRITING TO FILE!')

    def mark_message(self, key):
        """ Write a message to the director's log """

        messages = {'mccs': 'MCCS fault encountered',
                    'si': 'SI fault encountered',
                    'land': 'End of flight, packing up and sitting down',
                    'head': 'On heading, TOs setting up',
                    'target': 'On target, SI taking over',
                    'takeoff': 'Beginning of flight, getting set up',
                    'turn': 'Turning off target'}
        if key in messages.keys():
            self.line_stamper(messages[key])
        elif key == 'post':
            self.line_stamper(self.log_input_line.text())
            # Clear the line
            self.log_input_line.setText('')
        else:
            return

    def select_output_file(self):
        """
        Sets the filename of the Cruise Director log.

        Spawn the file chooser diaglog box and return the result, 
        attempting to both open and write to the file.
        Called when the 'Choose Output Filename' button on the 
        Cruise Director Log tab is pressed.
        """
        default_name = 'SILog_{0:s}'.format(
                                     self.utc_now.strftime('%Y%m%d.txt'))
        self.output_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                 'Save File',
                                                                 default_name)[0]
        if self.output_name != '':
            self.txt_log_output_name.setText('Writing to: {0:s}'.format(
                basename(str(self.output_name))))

    def select_log_output_file(self):
        """
        Sets the filename for the data log.

        Spawn the file chooser diaglog box and return the result, 
        attempting to both open and write to the file.
        Called when the 'Set Log Output File' button on the Data 
        Log tab is pressed.
        """
        default_name = 'DataLog_{0:s}'.format(
            self.utc_now.strftime('%Y%m%d.csv'))
        self.log_out_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                  'Save File',
                                                                  default_name)[0]
        if self.log_out_name != '':
            self.txt_data_log_save_file.setText('Writing to: {0:s}'.format(
                basename(str(self.log_out_name))))

    def post_log_line(self):
        """
        Writes a custom line to the Cruise Director Log.

        Records whatever is in the text box at the bottom of the 
        Cruise Director Log tab to the log file when the 'Post' 
        Button is pressed.
        """
        line = self.log_input_line.text()
        self.line_stamper(line)
        # Clear the line
        self.log_input_line.setText('')

    def count_direction(self, key):
        """
        Sets the direction the leg timer counts
        """
        if key == 'remain':
            self.do_leg_count_elapsed = False
            self.do_leg_count_remaining = True
        elif key == 'elapse':
            self.do_leg_count_elapsed = True
            self.do_leg_count_remaining = False
        else:
            # print('Invalid key in count_direction: {0:s}'.format(key))
            return

    def leg_timer(self, key):
        """
        Controls the timer for the leg
        """
        if key in 'start reset'.split():
            self.leg_counting = True
            time_stamp = datetime.datetime.now()
            self.timer_start_time = time_stamp.replace(microsecond=0)

            hms = self.leg_duration.time().toPyTime()
            # Calculate the time until the leg ends
            # If a fresh start or restart, pull from 
            # info about leg. If  the timer is paused 
            # (indicated by leg_counting_stopped==True),
            # get the new duration from the remaining time 
            # on the display
            if key == 'start' and self.leg_counting_stopped is True:
                dhour, dmin, dsec = [np.int(t) for t in
                                     self.txt_leg_timer.text().split(':')]
            else:
                dhour, dmin, dsec = hms.hour, hms.minute, hms.second

            duration = datetime.timedelta(hours=dhour,
                                          minutes=dmin,
                                          seconds=dsec)
            self.timer_end_time = self.timer_start_time + duration
            self.leg_counting_stopped = False
        elif key == 'stop':
            self.leg_counting = False
            self.leg_counting_stopped = True
        else:
            # print('Invalid key in leg_timer: {0:s}'.format(key))
            return

    def total_sec_to_hms_str(self, obj):
        """ Formats a datetime object into a time string """
        tsecs = obj.total_seconds()
        if tsecs < 0:
            isneg = True
            tsecs *= -1
        else:
            isneg = False
        hours = tsecs / 60. / 60.
        ihrs = np.int(hours)
        minutes = (hours - ihrs) * 60.
        imin = np.int(minutes)
        seconds = (minutes - imin) * 60.
        if isneg is True:
            done_str = '-{0:02d}:{1:02d}:{2:02.0f}'.format(ihrs, imin, seconds)
        else:
            done_str = '+{0:02d}:{1:02d}:{2:02.0f}'.format(ihrs, imin, seconds)
        return done_str

    def set_date_time_edit_boxes(self):
        """
        Initializes the takeoff/landing fields. 

        Intiially sets the fields to the current time, so we don't have
        to type in as much. The fields will be overwritten if a flight
        plan is read in. 
        """
        # Get the current time(s)
        self.update_times()
        # Get the actual displayed formatting string (set in the UI file)
        self.takeoff_time.displayFormat()
        self.landing_time.displayFormat()
        # Make the current time into a QDateTime object that we can display
        cur = QtCore.QDateTime.fromString(self.local_now_datetime_str,
                                          self.takeoff_time.displayFormat())
        # Actually put it in the box
        self.takeoff_time.setDateTime(cur)
        self.landing_time.setDateTime(cur)

    def flight_timer(self, key):
        """
        Starts MET and/or TTL timers
        """
        if key in 'met both'.split():
            self.met_counting = True
            self.takeoff = self.takeoff_time.dateTime().toPyDateTime()
            # Add tzinfo to this object to make it able to interact
            self.takeoff = self.takeoff.replace(tzinfo=self.localtz)
        if key in 'ttl both'.split():
            self.ttl_counting = True
            self.landing = self.landing_time.dateTime().toPyDateTime()
            # Add tzinfo to this object to make it able to interact
            self.landing = self.landing.replace(tzinfo=self.localtz)
        if self.ttl_counting is False and self.met_counting is False:
            # print('Invalid key in set_flight_timer: {0:s}'.format(key))
            return

    def update_times(self):
        """
        Determines the UTC/local time and fills the display strings. 

        We need to throw away microseconds so everything will count 
        together, otherwise it'll be out of sync due to microsecond 
        delay between triggers/button presses.
        Called during initialization of the app and at the beginning 
        of every showlcd loop.
        Sets:
            utc_now, utc_now_str, utc_now_datetime_str
            local_now, local_now_str, local_now_datetime_str
        """
        self.utc_now = datetime.datetime.utcnow()
        self.utc_now = self.utc_now.replace(microsecond=0)
        self.utc_now_str = self.utc_now.strftime(' %H:%M:%S UTC')
        self.utc_now_datetime_str = self.utc_now.strftime(
            '%m/%d/%Y %H:%M:%S $Z')

        # Safest way to sensibly go from UTC -> local timezone...?
        self.local_now = self.utc_now.replace(
            tzinfo=pytz.utc).astimezone(self.localtz)
        self.local_now_str = self.local_now.strftime(' %H:%M:%S %Z')
        self.local_now_datetime_str = self.local_now.strftime(
            '%m/%d/%Y %H:%M:%S')

    def show_lcd(self):
        """
        The main loop for the code.

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
        if self.met_counting is True:
            # Only runs if "Start MET" or "Start Both" button is pressed
            # Set the MET to show the time between now and takeoff
            local2 = self.local_now.replace(tzinfo=None)
            takeoff2 = self.takeoff.replace(tzinfo=None)
            self.met = local2 - takeoff2
            self.met_str = '{0:s} MET'.format(self.total_sec_to_hms_str(self.met))
            self.txt_met.setText(self.met_str)
        if self.ttl_counting is True:
            # Only runs if "Start TTL" or "Start Both" button is pressed
            # Sets the TTL to show the teim between landing and now
            # The timer is color-coded based on how long this time is:
            #     TTL > 2 hours = black
            #     1.5 < TTL < 2 hours = dark yellow
            #     TTL < 1.5 hours = red
            local2 = self.local_now.replace(tzinfo=None)
            landing2 = self.landing.replace(tzinfo=None)
            self.ttl = landing2 - local2
            self.ttl_str = '{0:s} TTL'.format(self.total_sec_to_hms_str(self.ttl))
            self.txt_ttl.setText(self.ttl_str)

            # Visual indicators setup; times are in seconds
            if self.ttl.total_seconds() >= 7200:
                self.txt_ttl.setStyleSheet('QLabel { color : black; }')

            elif 7200 > self.ttl.total_seconds() >= 5400:
                self.txt_ttl.setStyleSheet('QLabel { color : darkyellow; }')

            elif self.ttl.total_seconds() < 5400:
                self.txt_ttl.setStyleSheet('QLabel { color : red; }')

        if self.leg_counting is True:
            # Addresses the timer in the "Leg Timer" panel.
            # Only runs if the "Start" button in the "Leg Timer" 
            # panel is pressed
            local2 = self.local_now.replace(tzinfo=None)
            leg_end = self.timer_end_time.replace(tzinfo=None)
            leg_start = self.timer_start_time.replace(tzinfo=None)

            if self.do_leg_count_remaining is True:
                # Formats to Leg Timer to show how much time is remaining 
                # until the leg ends
                # The timer is color-coded based on how long this time is:
                #     Time left > 2 hours = black
                #     1.5 < Time left < 2 hours = dark yellow
                #     Time left < 1.5 hours = red
                self.leg_remain = leg_end - local2
                self.leg_remain_str = self.total_sec_to_hms_str(self.leg_remain)
                self.txt_leg_timer.setText(self.leg_remain_str)

                # Visual indicators setup
                if self.leg_remain.total_seconds() >= 3600:
                    self.txt_leg_timer.setStyleSheet('QLabel { color : black; }')
                elif 3600 > self.leg_remain.total_seconds() >= 2400:
                    self.txt_leg_timer.setStyleSheet(
                        'QLabel { color : darkyellow; }')
                elif self.leg_remain.total_seconds() < 2400:
                    self.txt_leg_timer.setStyleSheet('QLabel { color : red; }')

            if self.do_leg_count_elapsed is True:
                # Formats the Leg Timer to show how much time has elapsed
                self.leg_elapsed = local2 - leg_start
                self.leg_elapsed_str = self.total_sec_to_hms_str(
                    self.leg_elapsed)
                self.txt_leg_timer.setText(self.leg_elapsed_str)

        # Update the UTC and Local Clocks in the 'World Times' panel
        self.txt_utc.setText(self.utc_now_str)
        self.txt_local_time.setText(self.local_now_str)

        if self.start_data_log is True and \
                self.data_log_autoupdate.isChecked() is True:
            if self.utc_now.second % self.data_log_update_interval.value() == 0:
                # self.update_data_log()
                self.update_data()
                # print self.datatable

    def add_data_log_row(self):
        """
        Adds a blank row to the Data Log
        
        Called when the 'Add Blank Row' button in the Data Log tab is pressed.
        Alters table_datalog
        """
        row_position = self.table_data_log.rowCount()
        self.table_data_log.insertRow(row_position)
        self.data_filenames.append('--> ')
        # Actually set the labels for rows
        self.table_data_log.setVerticalHeaderLabels(self.data_filenames)
        self.data.write_to_file(self.log_out_name,self.headers)

    def del_data_log_row(self):
        """
        Removes a row from the Data Log
    
        Called when the 'Remove Highlighted Row' button in the Data Log 
        tab is pressed.
        Alters table_data_log
        """
        bad = self.table_data_log.currentRow()
        # -1 means we didn't select anything
        if bad != -1:
            # Clear the data we don't need anymore
            del self.data_filenames[bad]
            self.table_data_log.removeRow(self.table_data_log.currentRow())
            # Redraw
            self.table_data_log.setVerticalHeaderLabels(self.data_filenames)
            self.data.write_to_file(self.log_out_name,self.headers)

    def repopulate_data_log(self, rescan=False):
        """
        Recreates the data log table after keyword changes.

        After changing the column ordering or adding/removing keywords,
        use this to redraw the table in the new positions.
        Currently not working.
        """
        # Disable fun stuff while we update
        self.table_data_log.setSortingEnabled(False)
        self.table_data_log.horizontalHeader().setSectionsMovable(False)
        self.table_data_log.horizontalHeader().setDragEnabled(False)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.NoDragDrop)

        # thed_list = ['NOTES'] + self.headers
        thed_list = self.headers

        # First, grab the current table's contents
        tab_list = []
        for n in range(0, self.table_data_log.rowCount()):
            row_data = {}
            for m, hkey in enumerate(thed_list):
                if rescan is True:
                    # Need to somehow remap the basename'd row label to the
                    #   original listing of files (with path) to go rescan
                    fname = ''
                    row_data = header_dict(fname, self.headers,
                                           hdu=self.fitshdu)
                else:
                    rdat = self.table_data_log.item(n, m)
                    if rdat is not None:
                        row_data[hkey] = rdat.text()
                    else:
                        row_data[hkey] = ''
            tab_list.append(row_data)

        # Clear out the old data, since we could have rearranged columns
        self.table_data_log.clear()

        # Actually assign the new headers
        self.headers = self.new_headers

        # Update with the new number of columns
        self.table_data_log.setColumnCount(len(self.headers))
        self.table_data_log.setRowCount(len(tab_list))

        # Actually set the labels for rows
        self.table_data_log.setVerticalHeaderLabels(self.data_filenames)

        # Create the data table items and populate things
        for n, row in enumerate(tab_list):
            for m, hkey in enumerate(self.headers):
                try:
                    if row[hkey] == '':
                        # Field in the original table was empty
                        val = self.fill_space_from_header(n, hkey)
                    else:
                        # Field in the original table contained a value
                        val = row[hkey]
                except KeyError:
                    # Key not in the original table
                    val = self.fill_space_from_header(n, hkey)
                # Convert the value to a QTableWidgetItem object
                new_item = QtWidgets.QTableWidgetItem(val)
                # Add to the table
                self.table_data_log.setItem(n, m, new_item)

        # Update with the new column labels
        self.table_data_log.setHorizontalHeaderLabels(self.headers)

        # Resize to minimum required, then display
        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()

        # Seems to be more trouble than it's worth, so keep this commented
        #        self.table_datalog.setSortingEnabled(True)

        # Re-enable fun stuff
        self.table_data_log.horizontalHeader().setSectionsMovable(True)
        self.table_data_log.horizontalHeader().setDragEnabled(True)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.InternalMove)
        self.table_data_log.show()

        # Should add this as a checkbox option to always scroll to bottom
        #   whenever a new file comes in...
        self.table_data_log.scrollToBottom()

    def fill_space_from_header(self, n, hkey):
        """
        If a cell in the data_log is empty after a change in
        keyword headers, read through the file headers again
        to see if the keyword is there.
        """
        fname = self.data_filenames[n]
        try:
            val = '{0}'.format(self.data.header_vals[fname][hkey])
        except KeyError:
            val = ''
        return val

    def update_data(self):
        """
        Updates the data
        
        Reads in new FITS files and adds them to the header_vals
        """
        self.new_files = []
        # Get the current list of FITS files in the location
        if self.instrument == 'HAWCFlight':
            self.data_current = glob.glob(str(self.data_log_dir) + '/*.grabme')
        elif self.instrument == 'FIFI-LS':
            cur_data = []
            for root, dir_names, filenames in walk(str(self.data_log_dir)):
                for filename in fnmatch.filter(filenames, '*.fits'):
                    cur_data.append(join(root, filename))
            self.data_current = cur_data
        else:
            self.data_current = glob.glob(str(self.data_log_dir) + '/*.fits')
        bncur = [basename(x) for x in self.data_current]

        # Correct the file listing to be ordered by modification time
        self.data_current.sort(key=getmtime)

        if self.instrument == 'HAWCFlight':
            bnpre = [basename(x)[:-4] + 'grabme' for x in self.data_filenames]
        else:
            bnpre = [basename(x) for x in self.data_filenames]

        new_files = set(bncur) - set(bnpre)
        for fname in new_files:
            filename = join(self.data_log_dir, fname)
            self.data.add_image(filename, self.headers, hdu=self.fits_hdu)
            self.data_filenames.append(fname)
            self.new_files.append(fname)

        # If new files exist, update the table widget and 
        # write the new data to file    
        if len(new_files) > 0:
            self.update_table()
            if self.log_out_name != '':
                self.data.write_to_file(self.log_out_name, self.headers)

    def update_table(self):
        """
        Updates the table widget
        """

        # Disable table features during alteration
        self.table_data_log.setSortingEnabled(False)
        self.table_data_log.horizontalHeader().setSectionsMovable(False)
        self.table_data_log.horizontalHeader().setDragEnabled(False)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.NoDragDrop)

        # Add the data to the table
        # init_row_count = self.table_data_log.rowCount()
        # rows_to_add = len(self.new_files)
        # for n,(file_key,row) in enumerate(self.data.header_vals.items()):
        for n, file_key in enumerate(self.new_files):
            row_count = self.table_data_log.rowCount()
            self.table_data_log.insertRow(row_count)
            # for m,(key,val) in enumerate(row.items()):
            for m, key in enumerate(self.headers):
                val = self.data.header_vals[file_key][key]
                # val = row[key]
                item = QtWidgets.QTableWidgetItem(str(val))
                self.table_data_log.setItem(row_count,
                                            m, item)
                                            #m + 1, item)

        # Set the row labels
        self.table_data_log.setVerticalHeaderLabels(self.data_filenames)

        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()

        # Reenable features
        self.table_data_log.horizontalHeader().setSectionsMovable(True)
        self.table_data_log.horizontalHeader().setDragEnabled(True)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.InternalMove)
        self.table_data_log.show()

        self.table_data_log.scrollToBottom()

    def update_data_log(self):
        """
        Updates the Data Log.

        Called when either the 'Force Update' button in the Data Log 
        tab is pressed or at the end of the show_lcd loop if the 
        'Autoupdate every:' option is selected. 
        General notes:
          glob.glob returns a randomly ordered result, so that can 
          lead to jumbled results if you just use it blindly. Sort 
          by modification time to get a sensible listing. (can't use 
          creation time cross-platform)
        """
        # Get the current list of FITS files in the location
        if self.instrument == 'HAWCFlight':
            self.data_current = glob.glob(str(self.data_log_dir) + '/*.grabme')
        elif self.instrument == 'FIFI-LS':
            cur_data = []
            for root, dir_names, filenames in walk(str(self.data_log_dir)):
                for filename in fnmatch.filter(filenames, '*.fits'):
                    cur_data.append(join(root, filename))
            self.data_current = cur_data
        else:
            self.data_current = glob.glob(str(self.data_log_dir) + '/*.fits')

        # Correct the file listing to be ordered by modification time
        self.data_current.sort(key=getmtime)

        # Ok, lets try this beast again.
        #   Main difference here is the addition of a basename'd version
        #   of current and previous data. Maybe it's a network path bug?
        #   (grasping at any and all straws here)
        bncur = [basename(x) for x in self.data_current]

        if self.instrument == 'HAWCFlight':
            bnpre = [basename(x)[:-4] + 'grabme' for x in self.data_filenames]
        else:
            bnpre = [basename(x) for x in self.data_filenames]

        if len(bncur) != len(bnpre):
            self.data_new = []
            # Make the unique listing of old files
            s = set(bnpre)

            # Compare the new listing to the unique set of the old ones
            #   Previous logic was:
            #            diff = [x for x in self.data_current if x not in s]
            # Unrolled logic (might be easier to spot a goof-up)
            diff = []
            idxs = []
            for i, x in enumerate(bncur):
                if x not in s:
                    idxs.append(i)
                    diff.append(x)

            # Capture the last row position so we know where to start
            self.last_data_row = self.table_data_log.rowCount()

            # Actually query the files for the desired headers
            for idx in idxs:
                # REMEMBER: THIS NEEDS TO REFERENCE THE ORIGINAL LIST!
                if self.instrument == 'HAWCFlight':
                    realfile = self.data_current[idx][:-6] + 'fits'
                else:
                    realfile = self.data_current[idx]
                # Save the filenames
                self.data_filenames.append(basename(realfile))
                # Add number of rows for files to go into first
                row_position = self.table_data_log.rowCount()
                self.table_data_log.insertRow(row_position)
                # Actually get the header data
                the_data = header_dict(realfile, self.headers, hdu=self.fits_hdu)
                #                self.allData.append(theData)
                self.data_new.append(the_data)

            self.set_table_data()
            self.data.write_to_file(self.log_out_name,self.headers)

    def set_table_data(self):
        """ Writes data to table_data_log """
        if len(self.data_new) != 0:
            # Disable fun stuff while we update
            self.table_data_log.setSortingEnabled(False)
            self.table_data_log.horizontalHeader().setSectionsMovable(False)
            self.table_data_log.horizontalHeader().setDragEnabled(False)
            self.table_data_log.horizontalHeader().setDragDropMode(
                QtWidgets.QAbstractItemView.NoDragDrop)

            # Actually set the labels for rows
            self.table_data_log.setVerticalHeaderLabels(self.data_filenames)

            # Create the data table items and populate things
            #   Note! This is for use with header_dict style of grabbing stuff
            for n, row in enumerate(self.data_new):
                for m, hkey in enumerate(self.headers):
                    new_item = QtWidgets.QTableWidgetItem(str(row[hkey]))
                    self.table_data_log.setItem(n + self.last_data_row,
                                                m, new_item)
                                                #m + 1, new_item)

            # Resize to minimum required, then display
            self.table_data_log.resizeColumnsToContents()
            self.table_data_log.resizeRowsToContents()

            # Seems to be more trouble than it's worth, so keep this commented
            #            self.table_datalog.setSortingEnabled(True)

            # Reenable fun stuff
            self.table_data_log.horizontalHeader().setSectionsMovable(True)
            self.table_data_log.horizontalHeader().setDragEnabled(True)
            self.table_data_log.horizontalHeader().setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove)

            self.table_data_log.show()

            # Should add this as a checkbox option to always scroll to bottom
            #   whenever a new file comes in...
            self.table_data_log.scrollToBottom()
        else:
            print('No new files!')

#    def write_data_log(self):
#        """
#        Writes the data log to a csv file.
#
#        Runs after every update to the data log
#        """
#        print('Using wrong write function!')
#        sys.exit()
#        if self.log_out_name != '':
#            try:
#                f = open(self.log_out_name, 'w')
#                writer = csv.writer(f)
#                # Write the column labels first...assumes that the
#                #   filename and notes column are first and second
#                clabs = ['FILENAME', 'NOTES'] + self.headers
#                writer.writerow(clabs)
#                for row in range(self.table_data_log.rowCount()):
#                    row_data = [self.data_filenames[row]]
#                    for column in range(self.table_data_log.columnCount()):
#                        item = self.table_data_log.item(row, column)
#                        if item is not None:
#                            row_data.append(item.text())
#                        else:
#                            row_data.append('')
#                    writer.writerow(row_data)
#                f.close()
#            except IOError:
#                self.txt_data_log_save_file.setText('ERROR WRITING TO FILE!')

#        if self.log_out_name != '':
#            # fields = 'FILENAME NOTES'.split()+self.headers
#            fields = ['FILENAME']+self.headers
#            with open(self.log_out_name,'wb') as f:
#                w = csv.DictWriter(f, fields)
#                w.writeheader()
#                # Loop over filenames
#                for k in self.data.header_vals:
#                    row = {field: self.data.header_vals[k].get(field)
#                           for field in fields}
#                    row['FILENAME'] = k
#                    print(row)
#                    w.writerow(row)

    def leg_param_labels(self, key):
        """
        Toggle the visibility of the leg parameter labels
        """
        if key == 'on':
            self.txt_elevation.setVisible(True)
            self.txt_obs_plan.setVisible(True)
            self.txt_rof.setVisible(True)
            self.txt_target.setVisible(True)
        elif key == 'off':
            self.txt_elevation.setVisible(False)
            self.txt_obs_plan.setVisible(False)
            self.txt_rof.setVisible(False)
            self.txt_target.setVisible(False)
        else:
            # print('Invalid key in toggle_leg_param_labels: {0:s}'.format(key))
            return

    def toggle_leg_param_values_off(self):
        """
        Clears the leg parameter values.

        Usefule for dead/departure/arrival legs
        """
        self.leg_elevation.setText('')
        self.leg_obs_block.setText('')
        self.leg_rof_rof_rate.setText('')
        self.leg_target.setText('')

    def update_leg_info_window(self):
        """
        Displays details of flight plan parsed from .msi file.

        If the flight plan was successfully parsed, show the values
        for the leg occuring at self.legpos.
        """
        # Only worth doing if we read in a flight plan file
        if self.success_parse is True:
            # Quick and dirty way to show the leg type
            legtxt = '{0:d}\t{1:s}'.format(self.leg_pos + 1,
                                           self.leg_info.leg_type)
            self.leg_number.setText(legtxt)

            # Target name
            self.leg_target.setText(self.leg_info.target)

            # If the leg type is an observing leg, show the deets
            if self.leg_info.leg_type is 'Observing':
                self.leg_param_labels('on')
                elevation_label = '{0:.1f} to {1:.1f}'.format(
                    self.leg_info.range_elev[0],
                    self.leg_info.range_elev[1])
                self.leg_elevation.setText(elevation_label)
                rof_label = '{0:.1f} to {1:.1f} | {2:.1f} to {3:.1f}'.format(
                    self.leg_info.range_rof[0],
                    self.leg_info.range_rof[1],
                    self.leg_info.range_rofrt[0],
                    self.leg_info.range_rofrt[1])
                self.leg_rof_rof_rate.setText(rof_label)
#                try:
#                    self.leg_obs_block.setText(self.leginfo.obs_plan)
#                except:
#                    pass
            else:
                # If it's a dead leg, update the leg number and we'll move on
                # Clear values since they're probably crap
                self.toggle_leg_param_values_off()
                # Quick and dirty way to show the leg type
                # leg_txt = "%i\t%s" % (self.leg_pos + 1, self.leg_info.leg_type)
                leg_txt = '{0:d}\t{1:s}'.format(self.leg_pos + 1,
                                                self.leg_info.leg_type)
                self.leg_number.setText(leg_txt)

            # Now take the duration and autoset our timer duration
            time_parts = str(self.leg_info.duration).split(':')
            time_parts = [np.int(x) for x in time_parts]
            dur_time = QtCore.QTime(time_parts[0], time_parts[1], time_parts[2])
            self.leg_duration.setTime(dur_time)

    def prev_leg(self):
        """
        Move the leg position counter to the previous value.

        Bottoms out at 0
        """
        if self.success_parse is True:
            self.leg_pos -= 1
            if self.leg_pos < 0:
                self.leg_pos = 0
            self.leg_info = self.flight_info.legs[self.leg_pos]
        self.update_leg_info_window()

    def next_leg(self):
        """
        Move the leg position counter to the next value.

        Hits the ceiling at the max number of found legs
        """
        if self.success_parse is True:
            self.leg_pos += 1
            if self.leg_pos > self.flight_info.nlegs - 1:
                self.leg_pos = self.flight_info.nlegs - 1
            self.leg_info = self.flight_info.legs[self.leg_pos]
        else:
            pass
        self.update_leg_info_window()

    def update_flight_time(self, key):
        """
        Fills the takeoff or landing time fields

        Grab the flight takeoff time from the flight plan, which is in UTC,
        and turn it into the time at the local location.
        Then, take that time and update the DateTimeEdit box in the GUI
        """
        if key == 'takeoff':
            time = self.flight_info.takeoff.replace(tzinfo=pytz.utc)
        elif key == 'landing':
            time = self.flight_info.landing.replace(tzinfo=pytz.utc)
        else:
            # print('Invalid key in update_flight_time: {0:s}'.format(key))
            return
        time = time.astimezone(self.localtz)
        time_str = time.strftime('%m/%d/%Y %H:%M:%S')
        time_qt = QtCore.QDateTime.fromString(time_str, 'MM/dd/yyyy HH:mm:ss')
        if key == 'takeoff':
            self.takeoff_time.setDateTime(time_qt)
        else:
            self.landing_time.setDateTime(time_qt)

    def select_input_file(self):
        """
        Parses flight plan from .msi file. 

        Spawn the file chooser diaglog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).
        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance
        """
        self.fname = QtWidgets.QFileDialog.getOpenFileName()[0]
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
        self.flight_plan_filename.setStyleSheet('QLabel { color : black; }')
        self.flight_plan_filename.setText(basename(str(self.fname)))
        try:
            self.flight_info = fpmis.parseMIS(self.fname)
            self.leg_info = self.flight_info.legs[self.leg_pos]
            self.success_parse = True
            self.update_leg_info_window()
            if self.set_takeoff_fp.isChecked() is True:
                self.update_flight_time('takeoff')
            if self.set_landing_fp.isChecked() is True:
                self.update_flight_time('landing')
        except IOError:
            self.flight_info = ''
            self.err_msg = 'ERROR: Failure Parsing File!'
            self.flight_plan_filename.setStyleSheet('QLabel { color : red; }')
            self.flight_plan_filename.setText(self.err_msg)
            self.success_parse = False

    def browse_folder(self):
        """
        What is this function for?  Is it vestigial?  I don't remember
        this function or its purpose at all :-/
        """
        # In case there are any existing elements in the list
        self.listWidget.clear()
        title_str = 'Choose a SOFIA mission file (.mis)'
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               title_str)[0]

        # if user didn't pick a directory don't continue
        if directory:
            # for all files, if any, in the directory
            for file_name in listdir(directory):
                # add file to the listWidget
                self.listWidget.addItem(file_name)


class FITSKeyWordDialog(QtWidgets.QDialog, fkwp.Ui_FITSKWDialog):
    """
    Dialog box to allow for interactive selection of FITS keywords

    Currently non-functional
    """

    def __init__(self, parent=None):
        super(FITSKeyWordDialog, self).__init__(parent)

        self.setupUi(self)

        self.fitskw_add.clicked.connect(self.get_keyword_from_user)
        self.fitskw_remove.clicked.connect(self.remove_keyword_from_list)
        self.fitskw_model = self.fitskw_listing.model()
        self.fitskw_model.layoutChanged.connect(self.reordered_head_list)
        self.fitskw_savelist.clicked.connect(self.kw_save_list)
        self.fitskw_loadlist.clicked.connect(self.kw_load_list)
        self.fitskw_dialogbutts.accepted.connect(self.accept)
        self.fitskw_dialogbutts.rejected.connect(self.reject)
        self.utc_now = self.parent().utc_now

        # Grab a few things from the parent widget to use here
        self.headers = self.parentWidget().headers
        self.fits_hdu = self.parentWidget().fits_hdu
        self.reorder_kw_widget()
        self.update_head_list()

    def reordered_head_list(self):
        self.update_head_list()
        self.txt_fitskw_status.setText('Unsaved Changes!')

    def kw_save_list(self):
        self.select_kw_file(kind='save')
        if self.kwname != '':
            try:
                f = open(self.kwname, 'w')
                writer = csv.writer(f)
                rowdata = []
                for column in range(len(self.headers)):
                    if column is not None:
                        rowdata.append(str(self.headers[column]))
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)
                f.close()
                # statusline = "File Written: %s" % str(self.kwname)
                statusline = 'File Written: {0:s}'.format(self.kwname)
                self.txt_fitskw_status.setText(statusline)
            except Exception as why:
                print(str(why))
                self.txt_fitskw_status.setText('ERROR WRITING TO FILE!')

    def kw_load_list(self):
        self.select_kw_file(kind='load')
        if self.kwname != '':
            try:
                f = open(self.kwname, 'r')
                self.headers = []
                reader = csv.reader(f)
                for row in reader:
                    self.headers.append(row)
                statusline = 'File Loaded: {0:s}'.format(self.kwname)
                self.txt_fitskw_status.setText(statusline)
            except Exception as why:
                print(str(why))
                self.txt_fitskw_status.setText('ERROR READING THE FILE!')
            finally:
                f.close()
                # Loading could have left us with a list of lists, so flatten
                self.headers = list(itertools.chain(*self.headers))
                self.reorder_kw_widget()

    def reorder_kw_widget(self):
        self.fitskw_listing.clear()
        for key in self.headers:
            self.fitskw_listing.addItem(QtWidgets.QListWidgetItem(key))

    def get_keyword_from_user(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Add Keyword',
                                                  'New Keyword:',
                                                  QtWidgets.QLineEdit.Normal,
                                                  QtCore.QDir.home().dirName())
        text = str(text)
        if ok and text != '':
            text = text.strip()
            text = text.upper()
            self.fitskw_listing.addItem(QtWidgets.QListWidgetItem(text))
            self.headers.append(text)
            self.reorder_kw_widget()
            self.update_head_list()
            self.txt_fitskw_status.setText('Unsaved Changes!')

    def remove_keyword_from_list(self):
        for it in self.fitskw_listing.selectedItems():
            self.fitskw_listing.takeItem(self.fitskw_listing.row(it))
        self.txt_fitskw_status.setText('Unsaved Changes!')
        self.update_head_list()
        self.reorder_kw_widget()

    def select_kw_file(self, kind='save'):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to both open and write to the file.

        """
        defaultname = 'KWList_{0:s}{1:s}'.format(
            self.parentWidget().instrument,
            self.utc_now.strftime('_%Y%m%d.txt'))

        if kind == 'save':
            self.kwname = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                'Save File',
                                                                defaultname)[0]
        if kind == 'load':
            self.kwname = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                'Load File',
                                                                defaultname)[0]

    def update_head_list(self):
        self.headers = []
        for j in range(self.fitskw_listing.count()):
            ched = self.fitskw_listing.item(j).text()
            self.headers.append(str(ched))
        self.headers = [hlab.upper() for hlab in self.headers]


class FITSHeader():
    """
    Oversees the data structure that holds FITS headers
    """

    def __init__(self):

        # self.header_vals = {}
        self.header_vals = OrderedDict()

    def add_image(self, infile, hkeys, hdu=0):
        """
        Adds FITS header to data structure

        Opens the FITS file given by infile and selects out the
        headers contained in headers. Adds these values to 
        header_vals
        """
        header = OrderedDict()
        try:
            # Read in header from FITS
            head = pyf.getheader(infile, ext=hdu)
        except IOError:
            # Could not read file, return empty dictionary
            for key in hkeys:
                header[key] = ''
        else:
            # Select out the keywords of interest
            for key in hkeys:
                header[key] = head[key] if key in head else ''
        # Add to data structure with the filename as key
        self.header_vals[basename(infile)] = header

    def remove_image(self, infile):
        """
        Removes an observation form the data set
        """
        try:
            del self.header_vals[infile]
        except KeyError:
            print('Unable to remove {0:s} from header_vals'.format(infile))

    def write_to_file(self, outname, hkeys):
        """
        Writes data structure to outname
        """
        # f = open(outname, 'wb')
        # with open(outname, 'wb') as f:
        #    # fields = ['Filename,Notes'] + hkeys
        #    fields = ['Filename'] + hkeys
        #    w = csv.DictWriter(f, fields)
        #    w.writeheader()
        #    for k in self.header_vals:
        #        row = {field: self.header_vals[k].get(field) or k
        #               for field in fields}
        #        w.writerow(row)
        #    f.close()

        # if self.log_out_name != '':
        if outname != '':
            # fields = 'FILENAME NOTES'.split()+self.headers
            fields = ['FILENAME']+hkeys
            with open(outname,'wb') as f:
                w = csv.DictWriter(f, fields)
                w.writeheader()
                # Loop over filenames
                for k in self.header_vals:
                    row = {field: self.header_vals[k].get(field)
                           for field in fields}
                    row['FILENAME'] = k
                    w.writerow(row)


def header_list(infile, header_keys, hdu=0):
    """
    Given a FITS file and a list of header keywords of interest,
    parse those two together and return the result as a tuple of
    base filename and an sequential list of the keywords.
    """
    try:
        hed = pyf.getheader(infile, ext=hdu)
    except IOError:
        hed = ' '
    item = []
    for key in header_keys:
        try:
            item.append(hed[key])
        except KeyError:
            item.append('')

    return basename(infile), item


def header_dict(infile, header_keys, hdu=0):
    """
    Given a filename (fullpath), return a dict of the desired header keywords.
    """
    # Select out the headers from hed that are in headerlist
    # If that keyword is not in hed, fill the new dictionary with 
    # a blank string
    try:
        hed = pyf.getheader(infile, ext=hdu)
        item = {key: hed.get(key, '') for key in header_keys}
    except IOError:
        # Problem reading header, return an empty dictionary
        item = {key: '' for key in header_keys}
    # To avoid overlapping a possible FITS keyword named 'FILENAME', give
    # the filename the key of 'PhysicalFilename'
    item['PhysicalFilename'] = basename(infile)
    return item


def main():
    app = QtWidgets.QApplication(sys.argv)
    font = './SOFIACruiseTools/resources/fonts/digital_7/digital-7_mono.ttf'
    QtGui.QFontDatabase.addApplicationFont(font)
    form = SOFIACruiseDirectorApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()

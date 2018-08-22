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
import glob
import fnmatch
import datetime
import os
import matplotlib
matplotlib.use('QT5Agg')
import configobj as co
import pytz
import socket
import subprocess

try:
    from urllib.request import urlopen, URLError
except ImportError:
    # When using Python2
    from urllib2 import urlopen, URLError
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

try:
    import astropy.io.fits as pyf
except ImportError:
    import pyfits as pyf

import SOFIACruiseTools.support.mis_parser as fpmis
import SOFIACruiseTools.Director.SOFIACruiseDirectorPanel as scdp
from SOFIACruiseTools.Director.flightMap import FlightMap
from SOFIACruiseTools.Director.directorLog import DirectorLogDialog
from SOFIACruiseTools.Director.startupApp import StartupApp
from SOFIACruiseTools.Director.FITSKeyWordDialog import FITSKeyWordDialog
from SOFIACruiseTools.Director.fitsHeader import FITSHeader
from SOFIACruiseTools.Director.legTimer import LegTimerObj


try:
    from SOFIACruiseTools.header_checker.hcheck import file_checker as fc
except ImportError as e:
    print('\nEncountered {0} while importint header checker: '
          '\n\t{1}\n'.format(e.__class__.__name__, e))
    # Check that the directory is not empty
    target = './SOFIACruiseTools/header_checker/hcheck/file_checker.py'
    if os.path.isfile(target):
        # File exists, but not imported.
        # Check if __init__.py exists
        target = './SOFIACruiseTools/header_checker/__init__.py'
        if os.path.isfile(target):
            # Dunder init exists, but isn't being imported for some reason
            raise ImportError('Unable to import header_checker')
        else:
            # Dunder init is not there. Make it and try import again
            subprocess.call('touch {0}'.format(target), shell=True)
            try:
                from SOFIACruiseTools.header_checker.hcheck import file_checker as fc
            except ImportError:
                raise ImportError('Unable to import header_checker')
    else:
        raise ImportError('Header checker directory is empty.\n'
                          'Run:\n\tgit submodule update --init --recursive')

#try:
#    from ..header_checker.hcheck import file_checker as fc
#except ImportError as e:
#    print('Failed to import header_checker with {}'.format(e))
#    try:
#        from ..qa_tools.pyqatools.header_checker import file_checker as fc
#    except ImportError as e:
#        print('Failed to import qa_tools')
#        print('\nEncountered {0}: '
#              '\n\t{1}\n'.format(e.__class__.__name__, e))
#        print('Checking the symbolic link')
#        source = 'qa-tools'
#        link_name = './SOFIACruiseTools/qa_tools'
#        if not islink(link_name):
#            try:
#                symlink(source, link_name)
#                from ..qa_tools.pyqatools.header_checker import file_checker as fc
#            except (ImportError, OSError) as erro:
#                print('Cannot find header checker code.')
#                print('\nEncountered {0}: '
#                      '\n\t{1}\n'.format(erro.__class__.__name__, erro))
#                print('Verify that the git submodule has been properly pulled.')
#                print('In the top directory, run:')
#                print('\tgit submodule update --init --recursive')
#                print('\nTo avoid this error in the future, use '
#                      'the --recursive flag while cloning the repo')
#                sys.exit()
#        else:
#            print('Symbolic link connecting qa_tools to qa-tools already exists')
#            print('Unable to import qa_tools however')
#            print('Check the link is correct and qa-tools was '
#                  'pulled correctly with:')
#            print('\tgit submodule update --init --recursive')
#            sys.exit()


class ConfigError(Exception):
    """ Exception for errors in the config file """
    pass


class SOFIACruiseDirectorApp(QtWidgets.QMainWindow, scdp.Ui_MainWindow):
    """
    Main class for the Cruise Director
    """
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
        self.met_counting = False
        self.ttl_counting = False
        self.leg_count_remaining = True
        self.output_name = ''
        self.local_timezone = 'US/Pacific'
        self.localtz = pytz.timezone(self.local_timezone)
        self.set_date_time_edit_boxes()
        self.txt_met.setText('+00:00:00 MET')
        self.txt_ttl.setText('+00:00:00 TTL')
        self.data = FITSHeader()
        self.required_fields = ['NOTES', 'BADCAL', 'HEADER_CHECK']

        date = datetime.datetime.utcnow().strftime('%Y%m%d')
        self.header_check_warnings = 'header_check_{0:s}.log'.format(date)
        with open(self.header_check_warnings, 'w'):
            pass

        self.leg_timer = LegTimerObj()
        self.leg_timer.init_duration = None

        self.good_connection = True

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
        # Things are easier if the keywords are always in CAPS
        # The addition of the notes column happens in here
        self.update_table_cols()

        # Read config file
        try:
            self.config = co.ConfigObj('director.ini')
        except co.ConfigObjError:
            print('Cannot parse config file director.ini')
            print('Verify it is in the correct location '
                  'and formatted correctly.')
            sys.exit()
        self.verify_config()

        # Variables previously defined in function
        self.data_log_dir = ''
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
        self.new_files = None
        self.leg_info = None
        self.fname = None
        self.err_msg = None
        self.kwname = None
        self.new_headers = None
        self.flight_info = None
        self.checker = fc.FileChecker()
        self.checker_rules = None
        self.network_status = True
        self.network_status_hold = False
        self.network_status_control = True

        # Looks prettier with this stuff
        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()
        # Resize the Notes column, which should be
        # first column
        self.table_data_log.setColumnWidth(1, 10)

        # Actually show the table
        self.table_data_log.show()

        # Connect a signal to catch when the items in the table change
        self.table_data_log.itemChanged.connect(self.table_update)

        ####
        # Set up buttons
        ####

        self.toggle_network.clicked.connect(self.manual_toggle_network)

        # Control buttons
        self.setup_button.clicked.connect(self.setup)
        self.start_button.clicked.connect(self.start_run)
        self.end_button.clicked.connect(self.end_run)

        # Open the file chooser for the flight plan input
        # Flight plan progression
        self.leg_previous.clicked.connect(self.prev_leg)
        self.leg_next.clicked.connect(self.next_leg)
        # Start the flight progression timers
        self.set_takeoff_time.clicked.connect(lambda: self.flight_timer('met'))
        self.set_landing_time.clicked.connect(lambda: self.flight_timer('ttl'))
        self.set_takeoff_landing.clicked.connect(lambda:
                                                 self.flight_timer('both'))

        # Leg timer control
        self.time_select_remaining.clicked.connect(lambda:
                                                   self.count_direction('remain'))
        self.time_select_elapsed.clicked.connect(lambda:
                                                 self.count_direction('elapse'))
        self.leg_timer_start.clicked.connect(lambda:
                                             self.leg_timer.control_timer('start'))
        self.leg_timer_stop.clicked.connect(lambda:
                                            self.leg_timer.control_timer('stop'))
        self.leg_timer_reset.clicked.connect(lambda:
                                             self.leg_timer.control_timer('reset'))
        self.add_minute.clicked.connect(lambda:
                                        self.leg_timer.minute_adjust('add'))
        self.sub_minute.clicked.connect(lambda:
                                        self.leg_timer.minute_adjust('sub'))

        # Text log stuff
        self.log_input_line.returnPressed.connect(lambda: self.mark_message('post'))
        self.open_director_log.clicked.connect(self.popout_director_log)

        self.open_map.clicked.connect(self.open_flight_map)

        self.log_fault_mccs.clicked.connect(lambda: self.mark_message('mccs'))
        self.log_fault_si.clicked.connect(lambda: self.mark_message('si'))
        self.log_landing.clicked.connect(lambda: self.mark_message('land'))
        self.log_on_heading.clicked.connect(lambda: self.mark_message('head'))
        self.log_on_target.clicked.connect(lambda: self.mark_message('target'))
        self.log_takeoff.clicked.connect(lambda: self.mark_message('takeoff'))
        self.log_turning.clicked.connect(lambda: self.mark_message('turn'))
        self.log_post.clicked.connect(lambda: self.mark_message('post'))
        self.log_ignore.clicked.connect(lambda: self.mark_message('ignore'))

        self.data_log_flag_file.clicked.connect(self.flag_file)
        self.data_log_force_update.clicked.connect(self.fill_blanks)
        self.data_log_edit_keywords.clicked.connect(self.spawn_kw_window)
        self.data_log_add_row.clicked.connect(self.add_data_log_row)
        self.data_log_delete_row.clicked.connect(self.del_data_log_row)

        # Hide buttons that aren't needed anymore due to setup prompt
        self.set_takeoff_time.hide()
        self.set_landing_time.hide()
        self.set_takeoff_landing.hide()

        # Run the setup prompt
        self.update_times()
        self.setup()

        # Generic timer setup stuff
        timer = QtCore.QTimer(self)
        # Set up the time to run self.showlcd() every 500 ms
        timer.timeout.connect(self.show_lcd)
        timer.start(500)
        self.show_lcd()

    def verify_config(self):
        """
        Checks the config file director.ini
        Raises Config Error if there are inconsistencies
        """
        # Verify config is not empty
        if not self.config:
            raise ConfigError('Config empty. Verify director.ini'
                              ' is present and correctly formatted.')
        # Verify that all sections are present
        required_sections = ['keywords', 'search', 'sort',
                             'ttl_timer_hour_warnings',
                             'leg_timer_minute_warnings',
                             'network_test', 'flight_map']
        if len(required_sections) != len(self.config.keys()):
            raise ConfigError('Config missing keys')
        if set(required_sections) != set(self.config.keys()):
            raise ConfigError('Config missing keys')

        # Verify search methods are valid (either glob or walk)
        valid_methods = 'glob walk'.split()
        for instrument in self.config['search'].keys():
            method = self.config['search'][instrument]['method']
            if method not in valid_methods:
                raise ConfigError('Invalid search method for'
                                  ' {0:s}'.format(instrument))

        # Verify sort methods are valid (either name or time)
        valid_methods = 'name time'.split()
        for instrument in self.config['sort'].keys():
            method = self.config['sort'][instrument]
            if method not in valid_methods:
                raise ConfigError('Invalid sort method for'
                                  ' {0:s}'.format(instrument))

        # Verify first timer warning is longer than the second
        # timer warning for both TTL and leg timers
        try:
            first = float(self.config['ttl_timer_hour_warnings']['first'])
            second = float(self.config['ttl_timer_hour_warnings']['second'])
        except ValueError:
            raise ConfigError('Config TTL warnings must be numbers')
        else:
            if first < second:
                raise ConfigError('Config TTL timer warnings error: '
                                  'Second longer than first')
        try:
            first = float(self.config['leg_timer_minute_warnings']['first'])
            second = float(self.config['leg_timer_minute_warnings']['second'])
        except ValueError:
            raise ConfigError('Config leg warnings must be numbers')
        else:
            if first < second:
                raise ConfigError('Config leg timer warnings error: '
                                  'Second longer than first')

        # Check network test flags
        try:
            self.dns_check = int(self.config['network_test']['dns_check'])
            self.file_check = int(self.config['network_test']['file_check'])
        except ValueError:
            raise ConfigError('Unable to parse network_test settings')

        # Check map size setting
        try:
            self.map_width =  float(self.config['flight_map']['width'])
            self.marker_size = float(self.config['flight_map']['marker_size'])
        except ValueError:
            raise ConfigError('Unable to parse flight map settings.')

    def popout_director_log(self):
        """
        Pops open the director log in separate window
        """
        DirectorLogDialog(self)

    def open_flight_map(self):
        """Pops open the flight map"""
        FlightMap(self)

    def flag_file(self):
        """
        Updates "BADCAL" flag for the selected row

        When the "Flag File" on the Data Log tab is pressed, the "BADCAL" value
        for the selected row is set to "FLAG" in both the table and the
        background data structure.
        """
        row = self.table_data_log.currentRow()
        fname = self.data_filenames[row]
        flag_text = 'FLAG'
        flag_col = 'BADCAL'
        if self.data.header_vals[fname][flag_col]:
            flag_text = '{0:s}, {1:s}'.format(self.data.header_vals[fname][flag_col],
                                              flag_text)
            self.data.header_vals[fname][flag_col] = flag_text
        else:
            self.data.header_vals[fname][flag_col] = flag_text

        # Change the QtTable
        for column in range(self.table_data_log.columnCount()):
            header_text = self.table_data_log.horizontalHeaderItem(column).text()
            if header_text == 'BADCAL':
                self.table_data_log.setItem(row, column,
                                            QtWidgets.QTableWidgetItem(flag_text))
        # Update the widget with the new values
        self.repopulate_data_log()

    def fill_blanks(self):
        """
        Fills blanks in QtTableWidget

        Loops through the files in the background data structure and
        calls the fill_data_blank_cells method of the FITSHeader class
        to verify all header values that can be filled for the file are
        filled. Most useful for when a new FITS header keyword is added
        during the flight and previous observations need to be updated.
        """
        for fname in self.data.header_vals:
            filename = os.path.join(self.data_log_dir, fname)
            self.data.fill_data_blank_cells(filename, self.headers, self.fits_hdu)
        self.repopulate_data_log()

    def table_update(self, item):
        """
        Updates the data structure when the table is changed by the user

        This is called automatically whenever the QtTableWidget detects a
        change to its contents. Most likely this is due to a user manually
        changing a cell in the table. Gets the new value from the QtTableWidget
        and updates the background data structure.
        """
        # Change the value
        fname = self.table_data_log.verticalHeaderItem(item.row()).text()
        hkey = self.table_data_log.horizontalHeaderItem(item.column()).text()
        self.data.header_vals[fname][hkey] = item.text()

    def setup(self):
        """
        Prompts user for files needed to run program.

        Opens a dialog and prompts the user for the flight plan, location
        of data, where to write the data log to, where to write the director's
        log to, and the option to change the FITS keywords to use.
        """

        # Open the dialog
        window = StartupApp(self)
        result = window.exec_()

        if result:
            # Parse the results of the dialog.
            if not window.fname:
                self.flight_plan_filename.setStyleSheet('QLabel { color : red; }')

            # Local timezone
            # Do this first so the flight plan times are parsed
            # with the correct timezone
            self.local_timezone = window.local_timezone
            self.localtz = pytz.timezone(self.local_timezone)

            # Parse the flight plan
            self.parse_flight_file(window.fname)

            # Instrument
            self.instrument = window.instrument
            self.instrument_text.setText(self.instrument)
            #self.checker_rules = self.checker.choose_rules(self.instrument)

            # Data headers
            # Get the headers and set up the QtTableWidget
            self.headers = window.headers
            self.update_table_cols()
            self.table_data_log.resizeColumnsToContents()
            self.table_data_log.resizeRowsToContents()

            # Cruise Director Log filename
            # If this hasn't been set, change text to red as this
            # is required for the program to run
            if window.dirlog_name:
                self.output_name = window.dirlog_name
                self.txt_log_output_name.setText('{0:s}'.format(
                    os.path.basename(str(self.output_name))))
            else:
                self.txt_log_output_name.setStyleSheet('QLabel { color : red; }')
                return

            # Location of data
            if window.data_dir:
                self.data_log_dir = window.data_dir
                self.txt_data_log_dir.setText('{0:s}'.format(
                    self.data_log_dir))
                # Select header checker rules
                self.choose_head_check_rules()

            # Data Log filename
            if window.datalog_name:
                self.log_out_name = window.datalog_name
                self.txt_data_log_save_file.setText('{0:s}'.format(
                    os.path.basename(str(self.log_out_name))))

            # Log append flags
            if window.append_data_log:
                self.data.add_images_from_log(self.log_out_name, self.headers)
                self.update_table(append_init=True)
                #self.read_data_log()
            if window.append_director_log:
                self.read_director_log()
            #self.append_data_log = window.append_data_log
            #self.append_director_log = window.append_director_log
        
    def choose_head_check_rules(self, data_file=None):
        """
        Selects the rules for checking header values.
        """
        if not data_file:
            # Get a sample fits file from data directory
            config = self.config['search'][self.instrument]
            # Get the current list of FITS files in the location
            if config['method'] == 'glob':
                pattern = '{0:s}/*.{1:s}'.format(str(self.data_log_dir),
                                                 config['extension'])
                data_files = glob.glob(pattern)
                if data_files:
                    data_file = data_files[0]
                else:
                    self.checker_rules = None
                    return

            elif config['method'] == 'walk':
                pattern = '*.{0:s}'.format(config['extension'])
                current_data = []
                for root, _, filenames in os.walk(str(self.data_log_dir)):
                    for filename in fnmatch.filter(filenames, pattern):
                        data_file = os.path.join(root, filename)
                        break
                    break
            else:
                # Unknown method
                print('Unknown method {0:s} for instrument {1:s}'.format(
                    config['method'], self.instrument))
                self.checker_rules = None
                return

        # Pass it to self.checker.choose_rules
        rule = self.checker.choose_rules(data_file)

        # Set return value to self.checker_rules
        self.checker_rules = rule

    def start_run(self):
        """
        Starts the inner workings of the program.

        Flips the flags so the code starts looking for FITS files
        and starts the flight timers, but only if the Director Log
        output has been set up properly
        """
        if self.output_name:
            # Start collecting data
            self.start_data_log = True
            # Start MET and TTL timers
            self.flight_timer('both')
            self.instrument_text.setText(self.instrument)
        else:
            self.txt_log_output_name.setStyleSheet('QLabel { color : red; }')

    def end_run(self):
        """
        Ends the program

        Prompts the user for confirmation. If yes, write the data log and
        director log to file once again for good measure. Then close
        the app.
        """
        choice = QtWidgets.QMessageBox.question(self, 'Confirm',
                                                'Quit Cruise Director?',
                                                QtWidgets.QMessageBox.Yes |
                                                QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            # Write the data log and director log one last time
            self.data.write_to_file(self.log_out_name, self.headers)
            self.write_director_log()
            # Close the app
            self.close()

    def spawn_kw_window(self):
        """
        Opens the FITS Keywords select window.

        Called when the 'Edit Keywords...' button on the Data Log tab
        is pressed.
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
            for i, require in enumerate(self.required_fields):
                if require not in self.new_headers:
                    self.new_headers.insert(i, require)

            # Update the column data itself if we're actually logging
            if self.start_data_log is True:
                self.repopulate_data_log(rescan=True)

    def update_table_cols(self):
        """
        Updates the columns in the QTable Widget in the Data Log tab.

        Called initially when the window is first opened and again if the
        FITS keywords are changed. Due to the weird way the QtTableWidget
        works, the best way is to completely clear the table then remake it.
        """

        # Clear the table
        self.table_data_log.setColumnCount(0)
        self.table_data_log.setRowCount(0)

        # Add the number of columns we'll need for the header keys given
        for _ in self.headers:
            col_position = self.table_data_log.columnCount()
            self.table_data_log.insertColumn(col_position)
        self.table_data_log.setHorizontalHeaderLabels(self.headers)

    def line_stamper(self, line):
        """
        Updates the Cruise Director Log

        Appends a string given by line to the Director Log after
        it has been properly formatted by adding the UTC time and data
        stamp to the beginning. The line is added to both the GUI Log
        and the background list.
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
        self.write_director_log()

    def write_director_log(self):
        """
        Writes the cruise_log to file

        Dumps the contents of the background list, cruise_log, to
        the file specified by output_name. If any error occurs,
        change the name of the output file on the GUI to an error
        message.
        """
        if self.output_name:
            try:
                with open(self.output_name, 'w') as f:
                    f.writelines(self.cruise_log)
            except IOError:
                self.txt_log_output_name.setText('ERROR WRITING TO FILE!')

    def read_director_log(self):
        """
        Reads in existing director log.

        Called if the user wants to append an existing director log
        to the new log. 
        """
        print('Reading director log')
        # Read in current log
        try:
            with open(self.output_name,'r') as f:
                existing_log = f.readlines()
        except IOError:
            print('Unable to read existing director log:')
            #print(f'\t{self.output_name}')
            print('\t{0:s}'.format(self.output_name))
            print('Quitting')
            sys.exit()

        #print(f'Found {len(existing_log)} lines')
        # Add to current log
        for line in existing_log:
            self.cruise_log.append(line)
            self.log_display.append(line.strip())

    def mark_message(self, key):
        """
        Write a message to the director's log

        Accepts a key which determines what the message will be.
        The key sent is determined by which quick-log button is
        pressed. If no key is sent, do nothing.
        Regardless of the contents of the  message, sent it to
        line_stamper for the addition of the time stamp and for
        it to be added to the actual logs.
        """

        messages = {'mccs': 'MCCS fault encountered',
                    'si': 'SI fault encountered',
                    'land': 'End of flight, packing up and sitting down',
                    'head': 'On heading, TOs setting up',
                    'target': 'On target, SI taking over',
                    'takeoff': 'Beginning of flight, getting set up',
                    'turn': 'Turning off target',
                    'ignore': 'Ignore the previous message'}

        if key in messages.keys():
            self.line_stamper(messages[key])
        elif key == 'post':
            self.line_stamper(self.log_input_line.text())
            # Clear the line
            self.log_input_line.setText('')
        else:
            return

    def post_log_line(self):
        """
        Writes a custom line to the Cruise Director Log.

        Records whatever is in the text box at the bottom of the
        Cruise Director Log tab to the log file when the 'Post'
        Button is pressed.
        """
        line = self.log_input_line.text()
        # If this line is empty, try to pull from the text field
        # on the Data Log tab
        if not line:
            line = self.log_line_director.text()
        self.line_stamper(line)
        # Clear the line
        self.log_input_line.setText('')

    def read_data_log(self):
        """
        Reads existing data log
        """

    def count_direction(self, key):
        """
        Sets the direction the leg timer counts

        Accepts a key that's determined by which button is pressed
        in the Leg Timer panel of the main UI.
        """
        if key == 'remain':
            # self.do_leg_count_elapsed = False
            self.leg_count_remaining = True
        elif key == 'elapse':
            # self.do_leg_count_elapsed = True
            self.leg_count_remaining = False
        else:
            return

    def set_date_time_edit_boxes(self):
        """
        Initializes the takeoff/landing fields.

        Initially sets the fields to the current time, so we don't have
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
            self.takeoff = self.localtz.localize(self.takeoff)
        if key in 'ttl both'.split():
            self.ttl_counting = True
            self.landing = self.landing_time.dateTime().toPyDateTime()
            # Add tzinfo to this object to make it able to interact
            self.landing = self.localtz.localize(self.landing)
        if self.ttl_counting is False and self.met_counting is False:
            return

    def update_times(self):
        """
        Determines the UTC/local time and fills the display strings.

        We need to throw away microseconds so everything will count
        together, otherwise it'll be out of sync due to microsecond
        delay between triggers/button presses.
        Called during initialization of the app and at the beginning
        of every show_lcd loop.
        """
        self.utc_now = datetime.datetime.utcnow()
        self.utc_now = self.utc_now.replace(microsecond=0)
        self.utc_now_str = self.utc_now.strftime(' %H:%M:%S UTC')
        self.utc_now_datetime_str = self.utc_now.strftime(
            '%m/%d/%Y %H:%M:%S $Z')

        # Safest way to sensibly go from UTC -> local timezone...?
        utc = pytz.utc.localize(self.utc_now)
        self.local_now = utc.astimezone(self.localtz)
        #self.local_now = self.utc_now.replace(
        #    tzinfo=pytz.utc).astimezone(self.localtz)
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
            # Set the MET to show the time between now and takeoff
            local2 = self.local_now.replace(tzinfo=None)
            takeoff2 = self.takeoff.replace(tzinfo=None)
            self.met = local2 - takeoff2
            #self.met = self.local_now - self.takeoff
            self.met_str = '{0:s} MET'.format(total_sec_to_hms_str(self.met))
            self.txt_met.setText(self.met_str)
        if self.ttl_counting is True:
            # Only runs if "Start TTL" or "Start Both" button is pressed
            # Sets the TTL to show the teim between landing and now
            # The timer is color-coded based on how long this time is
            local2 = self.local_now.replace(tzinfo=None)
            landing2 = self.landing.replace(tzinfo=None)
            self.ttl = landing2 - local2
            self.ttl_str = '{0:s} TTL'.format(total_sec_to_hms_str(self.ttl))
            self.txt_ttl.setText(self.ttl_str)

            # Visual indicators setup; times are in seconds
            timer_warnings = self.config['ttl_timer_hour_warnings']
            first_warning = float(timer_warnings['first'])*3600.
            second_warning = float(timer_warnings['second'])*3600.
            if self.ttl.total_seconds() >= first_warning:
                self.txt_ttl.setStyleSheet('QLabel { color : black; }')
            elif self.ttl.total_seconds() >= second_warning:
                self.txt_ttl.setStyleSheet('QLabel { color : darkyellow; }')
            else:
                self.txt_ttl.setStyleSheet('QLabel { color : red; }')

        if self.leg_timer.status == 'running':
            # Addresses the timer in the "Leg Timer" panel.
            # Only runs if the "Start" button in the "Leg Timer"
            # panel is pressed
            if self.leg_count_remaining:
                time_string = self.leg_timer.timer_string('remaining')
                self.leg_timer_color(self.leg_timer.remaining.total_seconds())
            else:
                time_string = self.leg_timer.timer_string('elapsed')
            self.txt_leg_timer.setText(time_string)

        # Update the UTC and Local Clocks in the 'World Times' panel
        self.txt_utc.setText(self.utc_now_str)
        self.txt_local_time.setText(self.local_now_str)

        # Update the network test flag
        if (self.dns_check or self.file_check) and self.network_status_control:
            self.verify_network()
            self.network_status_display_update()
        else:
            self.network_status_display_update(stop=True)
            

        # If the program is set to look for data automatically and the time
        # is a multiple of the update frequency and network is good
        if self.start_data_log and self.data_log_autoupdate.isChecked():
            if self.utc_now.second % self.data_log_update_interval.value() == 0:
                # If the network is good or if the user has turned off
                # checking the network
                if self.network_status or not self.network_status_control:
                    self.update_data()

    def manual_toggle_network(self):
        """ Test button to toggle network status. """
        #self.verify_network(testing=True)
        if self.network_status_control:
            self.network_status_display_update()
            self.network_status_control = not self.network_status_control
        else: 
            self.network_status_display_update(stop=True)
            self.network_status_control = not self.network_status_control
        #self.network_status_hold = not self.network_status_hold

    def verify_network(self, host='8.8.8.8', port=53, 
                       timeout=3, testing=False):
        """ Tests the current status of the network.

        Checks if Google can be pinged and if the data
        directory is still available. If not, set 
        good_conenction flag low to pause data collection.
        """
        google_ipaddr = '296.58.192.142'
        address = 'https://{0:s}'.format(google_ipaddr)
        if testing:
            self.network_status = not self.network_status
        elif self.network_status_hold:
            pass
        else:
            if os.path.isdir(self.data_log_dir):
                try:
                    socket.setdefaulttimeout(timeout)
                    socket.socket(socket.AF_INET, 
                                  socket.SOCK_STREAM).connect((host,port))
                    #print('socket success')
                    self.network_status = True
                except Exception as ex:
                    print(ex)
                    self.network_status = False
            else:
                self.network_status = False

    def network_status_display_update(self, stop=False):
        """ Updates the GUI status with current network status """
        style = 'QLabel {{color : {0:s}; }}'
        if stop:
            self.network_status_display.setText('Not testing network')
            self.network_status_display.setStyleSheet(style.format('black'))
        else:
            if self.network_status:
                self.network_status_display.setText('Network Good')
                self.network_status_display.setStyleSheet(style.format('green'))
            else:
                self.network_status_display.setText('Network Bad')
                self.network_status_display.setStyleSheet(style.format('red'))

    def leg_timer_color(self, remaining_seconds):
        """
        Sets the color of the leg timer

        Limits of when different colors are applied come from
        the config file.
        """

        timer_warnings = self.config['leg_timer_minute_warnings']
        first_warning = float(timer_warnings['first'])*60
        second_warning = float(timer_warnings['second'])*60

        # Visual indicators setup
        if remaining_seconds >= first_warning:
            self.txt_leg_timer.setStyleSheet('QLabel { color : black; }')
        elif remaining_seconds >= second_warning:
            self.txt_leg_timer.setStyleSheet(
                'QLabel { color : orange; }')
        else:
            self.txt_leg_timer.setStyleSheet('QLabel { color : red; }')

    def add_data_log_row(self):
        """
        Adds a blank row to the Data Log

        Called when the 'Add Blank Row' button in the Data Log tab is pressed.
        """

        # Add the blank row to the data structure
        self.data.add_blank_row(self.headers)

        self.table_data_log.blockSignals(True)

        row_position = self.table_data_log.rowCount()
        self.table_data_log.insertRow(row_position)
        self.data_filenames.append('blank_{0:d}'.format(self.data.blank_count))
        # Actually set the labels for rows
        self.table_data_log.setVerticalHeaderLabels(self.data_filenames)
        self.data.write_to_file(self.log_out_name, self.headers)

        self.table_data_log.blockSignals(False)

    def del_data_log_row(self):
        """
        Removes a row from the Data Log

        Called when the 'Remove Highlighted Row' button in the Data Log
        tab is pressed.
        """
        bad = self.table_data_log.currentRow()
        # -1 means we didn't select anything
        if bad != -1:
            self.table_data_log.blockSignals(True)
            # Clear the data we don't need anymore
            self.data.remove_image(self.data_filenames[bad])
            del self.data_filenames[bad]
            self.table_data_log.removeRow(bad)
            # Redraw
            self.table_data_log.setVerticalHeaderLabels(self.data_filenames)
            self.data.write_to_file(self.log_out_name, self.headers)
            self.table_data_log.blockSignals(False)

    def repopulate_data_log(self, rescan=False):
        """
        Recreates the data log table after keyword changes.

        This is called after changing keywords, blanks are filled,
        or a file has been flagged.
        """
        # Disable fun stuff while we update
        self.table_data_log.setSortingEnabled(False)
        self.table_data_log.horizontalHeader().setSectionsMovable(False)
        self.table_data_log.horizontalHeader().setDragEnabled(False)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.NoDragDrop)
        self.table_data_log.blockSignals(True)

        thed_list = self.headers

        # First, grab the current table's contents
        tab_list = []
        for n in range(0, self.table_data_log.rowCount()):
            row_data = {}
            for m, hkey in enumerate(thed_list):
                rdat = self.table_data_log.item(n, m)
                if rdat is not None:
                    row_data[hkey] = rdat.text()
                else:
                    row_data[hkey] = ''
            tab_list.append(row_data)

        # Clear out the old data, since we could have rearranged columns
        self.table_data_log.clear()

        # Actually assign the new headers
        if rescan:
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
        self.table_data_log.blockSignals(False)

        # Should add this as a checkbox option to always scroll to bottom
        #   whenever a new file comes in...
        self.table_data_log.scrollToBottom()

    def fill_space_from_header(self, n, hkey):
        """
        Attempts to fill an empty cell in the QtTableWidget

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
        Looks for new observations

        Reads in new FITS files and adds them to the header_vals
        """

        # Each instrument can store their data in a different way.
        # Read in the correct method to use from the
        # director.ini config file
        config = self.config['search'][self.instrument]
        self.new_files = []
        # Get the current list of FITS files in the location
        if config['method'] == 'glob':
            if self.instrument.lower() == 'forcast':
                # FORCAST has 2 channels, r and b. While not used at the
                # same time, they are often used in the same flight. To prevent
                # restarting Cruise Director every time, the data_log_dir
                # is set to the parent directory and new files are pulled from
                # both the r and b subdirectories.
                pattern = '{0:s}/[rb]/*.{1:s}'.format(str(self.data_log_dir),
                                                      config['extension'])
            else:
                pattern = '{0:s}/*.{1:s}'.format(str(self.data_log_dir),
                                                 config['extension'])
            self.data_current = glob.glob(pattern)
        elif config['method'] == 'walk':
            pattern = '*.{0:s}'.format(config['extension'])
            current_data = []
            for root, _, filenames in os.walk(str(self.data_log_dir)):
                for filename in fnmatch.filter(filenames, pattern):
                    current_data.append(os.path.join(root, filename))
            self.data_current = current_data
        else:
            # Unknown method
            print('Unknown method {0:s} for instrument {1:s}'.format(
                config['method'], self.instrument))
            return

        # Correct the file listing to be ordered by modification time
        self.data_current = self.sort_files(self.data_current)

        bncur = [os.path.basename(x) for x in self.data_current]
        if self.instrument == 'HAWCFlight':
            bnpre = [os.path.basename(x)[:-4] + 'grabme' for x in self.data_filenames]
        else:
            bnpre = [os.path.basename(x) for x in self.data_filenames]

        # Separate out the new files
        new_files = set(bncur) - set(bnpre)
        if self.instrument.lower() == 'forcast':
            new_files = [os.path.join(self.data_log_dir, i[0], i)
                         for i in new_files]
        else:
            new_files = [os.path.join(self.data_log_dir, i) for i in new_files]
        new_files = self.sort_files(new_files)
        for fname in new_files:
            if not self.checker_rules:
                self.choose_head_check_rules(data_file=fname)
            self.data.add_image(fname, self.headers, self.header_check_warnings,
                                hdu=self.fits_hdu, rules=self.checker_rules)
            bname = os.path.basename(fname)
            self.data_filenames.append(bname)
            self.new_files.append(bname)

        # If new files exist, update the table widget and
        # write the new data to file
        if new_files:
            self.update_table()
            if self.log_out_name != '':
                self.data.write_to_file(self.log_out_name, self.headers)

    def sort_files(self, files):
        """
        Sort files based on method in config

        Takes in the a list of files and sorts them. If there
        are problems, exit.
        """
        if self.config['sort'][self.instrument] == 'time':
            return sorted(files, key=os.path.getmtime)
        elif self.config['sort'][self.instrument] == 'name':
            if self.instrument.lower() == 'forcast':
                return sorted(files, key=lambda x:
                        int(os.path.basename(x).split('_')[-1].split('.')[0]))
                        #int(x.split(os.path.sep)[-1].split('_')[1].split('.')[0]))
            else:
                print('Unknown file formatting for {0:s}'.format(self.instrument))
                print('Cannot sort')
                sys.exit()
        else:
            print('Unknown file sorting method. Check config file, director.ini')
            sys.exit()

    def update_table(self, append_init=False):
        """
        Updates the table widget to display newly found files
        """

        # Disable table features during alteration
        self.table_data_log.setSortingEnabled(False)
        self.table_data_log.horizontalHeader().setSectionsMovable(False)
        self.table_data_log.horizontalHeader().setDragEnabled(False)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.NoDragDrop)
        self.table_data_log.blockSignals(True)

        if append_init:
            self.new_files = self.data.header_vals.keys()
            self.data_filenames = self.data.header_vals.keys()

        # Add the data to the table
        for file_key in self.new_files:
            row_count = self.table_data_log.rowCount()
            self.table_data_log.insertRow(row_count)
            for m, key in enumerate(self.headers):
                val = self.data.header_vals[file_key][key]
                item = QtWidgets.QTableWidgetItem(str(val))
                if key == 'HEADER_CHECK' and val == 'Failed':
                    # Set text to red
                    item.setForeground(QtGui.QColor(255, 0, 0))
                self.table_data_log.setItem(row_count, m, item)

        # Set the row labels
        self.table_data_log.setVerticalHeaderLabels(self.data_filenames)

        self.table_data_log.resizeColumnsToContents()
        self.table_data_log.resizeRowsToContents()

        # Re-enable features
        self.table_data_log.horizontalHeader().setSectionsMovable(True)
        self.table_data_log.horizontalHeader().setDragEnabled(True)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.InternalMove)
        self.table_data_log.show()
        self.table_data_log.blockSignals(False)

        self.table_data_log.scrollToBottom()

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
            return

    def toggle_leg_param_values_off(self):
        """
        Clears the leg parameter values.

        Useful for dead/departure/arrival legs
        """
        self.leg_elevation.setText('')
        self.leg_obs_block.setText('')
        self.leg_rof_rof_rate.setText('')
        self.leg_target.setText('')

    def update_leg_info_window(self):
        """
        Displays details of flight plan parsed from .msi file.

        If the flight plan was successfully parsed, show the values
        for the leg occurring at self.legpos.
        """
        # Only worth doing if we read in a flight plan file
        if self.success_parse:
            # Quick and dirty way to show the leg type
            leg_labels = 'landing departure science dead'.split()
            if self.leg_info.leg_type.lower() not in leg_labels:
                leg_label = 'Other'
            else:
                leg_label = self.leg_info.leg_type
            legtxt = '{0:d}\t{1:s}'.format(self.leg_pos + 1,
                                           leg_label.capitalize())
            self.leg_number.setText(legtxt)

            # Target name
            self.leg_target.setText(self.leg_info.astro.target)

            # If the leg type is an observing leg, show the deets
            # if self.leg_info.leg_type == 'Observing':
            if self.leg_info.leg_type == 'science':
                self.leg_param_labels('on')
                elevation_label = '{0:.1f} to {1:.1f}'.format(
                    self.leg_info.plane.elevation_range[0],
                    self.leg_info.plane.elevation_range[1])
                self.leg_elevation.setText(elevation_label)
                rof_label = '{0:.1f} to {1:.1f} | {2:.1f} to {3:.1f}'.format(
                    self.leg_info.plane.rof_range[0],
                    self.leg_info.plane.rof_range[1],
                    self.leg_info.plane.rof_rate_range[0],
                    self.leg_info.plane.rof_rate_range[1])
                self.leg_rof_rof_rate.setText(rof_label)
                try:
                    self.leg_obs_block.setText(self.leg_info.obs_plan)
                except AttributeError:
                    pass
            else:
                # If it's a dead leg, update the leg number and we'll move on
                # Clear values since they're probably crap
                self.toggle_leg_param_values_off()

            # Update leg_timer
            # Now take the duration and autoset our timer duration
            time_parts = str(self.leg_info.duration).split(':')
            time_parts = [np.int(x) for x in time_parts]
            dur_time = datetime.time(hour=time_parts[0], minute=time_parts[1],
                                     second=time_parts[2])
            self.leg_duration.setTime(dur_time)
            dur_time = datetime.timedelta(hours=dur_time.hour,
                                          minutes=dur_time.minute,
                                          seconds=dur_time.second)
            self.leg_timer.duration = dur_time
            self.leg_timer.init_duration = dur_time

            # Set the timing parameters display
            self.leg_dur_from_mis.setText(str(self.leg_info.duration))
            self.leg_start_from_mis.setText(str(self.leg_info.start))
            self.leg_timer.flight_parsed = True

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
        self.leg_timer.status = 'stopped'

    def next_leg(self):
        """
        Move the leg position counter to the next value.

        Hits the ceiling at the max number of found legs
        """
        if self.success_parse is True:
            self.leg_pos += 1
            if self.leg_pos > self.flight_info.num_legs - 1:
                self.leg_pos = self.flight_info.num_legs - 1
            self.leg_info = self.flight_info.legs[self.leg_pos]
        else:
            pass
        self.update_leg_info_window()
        self.leg_timer.status = 'stopped'

    def update_flight_time(self, key):
        """
        Fills the takeoff or landing time fields

        Grab the flight takeoff time from the flight plan, which is in UTC,
        and turn it into the time at the local location.
        Then, take that time and update the DateTimeEdit box in the GUI
        """
        if key == 'takeoff':
            time = pytz.utc.localize(self.flight_info.takeoff)
        elif key == 'landing':
            time = self.flight_info.landing.replace(tzinfo=pytz.utc)
        else:
            return
        time = time.astimezone(self.localtz)
        time_str = time.strftime('%m/%d/%Y %H:%M:%S')
        time_qt = QtCore.QDateTime.fromString(time_str, 'MM/dd/yyyy HH:mm:ss')
        if key == 'takeoff':
            self.takeoff_time.setDateTime(time_qt)
        else:
            self.landing_time.setDateTime(time_qt)

    def parse_flight_file(self, from_gui=None):
        """
        Parses flight plan from .msi file.

        Spawn the file chooser dialog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).
        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance
        """
        # If from_gui is None, prompt the user to select a filename
        if not from_gui:
            self.fname = ''
        else:
            self.fname = from_gui
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
        self.flight_plan_filename.setStyleSheet('QLabel { color : black; }')
        self.flight_plan_filename.setText(os.path.basename(str(self.fname)))
        try:
            # self.flight_info = fpmis.parseMIS(self.fname)
            self.flight_info = fpmis.parse_mis_file(self.fname)
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


def total_sec_to_hms_str(obj):
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


def main():
    """ Generate the gui and run """
    app = QtWidgets.QApplication(sys.argv)
    font = './SOFIACruiseTools/resources/fonts/digital_7/digital-7_mono.ttf'
    QtGui.QFontDatabase.addApplicationFont(font)
    form = SOFIACruiseDirectorApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()

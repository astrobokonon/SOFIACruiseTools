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
import logging
import logging.config
import subprocess
import cartopy

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

        #config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        #                                                           'log.conf')
        #logging.config.fileConfig(config_file)
        #self.logger = logging.getLogger('default')

        self.logger = logging.getLogger('default')
        self.logger.info('Read in log default')

        self.pass_style = 'QLabel { color : black; }'
        self.warn_style = 'QLabel { color : orange; }'
        self.fail_style = 'QLabel { color : red; }'

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
        self.dns_check = 0
        self.file_check = 1
        self.sample_rate = 2
        self.map_width = 15
        self.marker_size = 10
        self.update_freq = 5

        # Read config file
        try:
            self.config = co.ConfigObj('director.ini')
        except co.ConfigObjError:
            message = ('Cannot parse config file director.ini\n'
                       'Verify it is in the correct location '
                       'and formatted correctly.')
            raise co.ConfigObjError(message)

        self.verify_config()

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
        self.logger.info('Starting button setup')

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
        #self.leg_timer_reset.clicked.connect(lambda:
        #                                     self.leg_timer.control_timer('reset'))
        self.leg_timer_reset.clicked.connect(lambda:
                                             self.update_duration(reset=True))
        self.add_minute.clicked.connect(lambda:
                                        self.leg_timer.minute_adjust('add'))
        self.sub_minute.clicked.connect(lambda:
                                        self.leg_timer.minute_adjust('sub'))
        self.leg_timer_update.clicked.connect(self.update_duration)
        #self.leg_duration.timeChanged(self.update_duration())

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
        self.logger.info('Running setup prompt')
        self.update_times()
        self.setup()

        self.setup_leg_map()
        self.plot_leg()

        self.logger.info('Starting loop')
        # Generic timer setup stuff
        timer = QtCore.QTimer(self)
        # Set up the time to run self.showlcd() every 500 ms
        timer.timeout.connect(self.show_lcd)
        timer.start(500)
        self.show_lcd()

    def setup_leg_map(self):
        """Set up the small map of the current leg."""
        code_location = os.path.dirname(os.path.realpath(__file__))
        cartopy.config['pre_existing_data_dir'] = os.path.join(code_location,
                                                               'maps')

        print(self.leg_pos)
        steps = self.flight_info.steps.points[self.flight_info.steps.points[
                                                  'leg_num'] == self.leg_pos+1]
        print(steps)

        standard_longitudes = np.arange(-180, 181, 5)
        med_lat = np.median(steps['latitude'])
        med_lon = np.median(steps['longitude'])
        print(med_lat, med_lon)

        # Extra degrees to pad map
        extent = (np.min(steps['longitude'])-self.map_width,
                  np.max(steps['longitude'])+self.map_width,
                  np.min(steps['latitude'])-self.map_width,
                  np.max(steps['latitude'])+self.map_width)

        ortho = cartopy.crs.Orthographic(central_latitude=med_lat,
                                         central_longitude=med_lon)
        self.leg_map.canvas.figure.clf()
        pos = [0.01, 0.01, 0.98, 0.98]    # left, bottom, width, height
        self.leg_map.canvas.ax = self.leg_map.canvas.figure.add_subplot(111,
                                                                 projection=ortho,
                                                                 position=pos)
        # Set limits
        self.leg_map.canvas.ax.set_extent(extent)
        # Turn on coastlines and other geographic features
        self.leg_map.canvas.ax.coastlines(resolution='110m',
                                                  edgecolor='red',
                                                  linewidth=0.75)
        self.leg_map.canvas.ax.add_feature(cartopy.feature.OCEAN)
        self.leg_map.canvas.ax.add_feature(cartopy.feature.LAND)
        self.leg_map.canvas.ax.add_feature(cartopy.feature.LAKES)
        self.leg_map.canvas.ax.add_feature(cartopy.feature.BORDERS,
                                                   edgecolor='red',
                                                   linewidth=0.75)
        # self.leg_map.canvas.ax.add_feature(cartopy.feature.COASTLINE)
        self.leg_map.canvas.ax.add_feature(cartopy.feature.RIVERS)
        states_name = 'admin_1_states_provinces_lakes_shp'
        states = cartopy.feature.NaturalEarthFeature(category='cultural',
                                                     name=states_name,
                                                     scale='110m',
                                                     facecolor='none')
        self.leg_map.canvas.ax.add_feature(states, edgecolor='black',
                                                   linewidth=0.75)
        # self.leg_map.canvas.ax.coastlines(color='black')

        # Set up plot parameters
        gl = self.leg_map.canvas.ax.gridlines(color='k', linestyle='--',
                                                      linewidth=0.2)
        gl.xlocation = matplotlib.ticker.FixedLocator(standard_longitudes)
        gl.xformatter = cartopy.mpl.gridliner.LONGITUDE_FORMATTER
        gl.yformatter = cartopy.mpl.gridliner.LATITUDE_FORMATTER

        self.leg_map.canvas.draw()

    def plot_leg(self, current=True):

        if self.use_current_leg.isChecked():
            leg_num = 0
        else:
            leg_num = self.leg_pos + 1
        steps = self.flight_info.steps.points[self.flight_info.steps.points[
                                                  'leg_num'] == self.leg_pos+1]
        lat = steps['latitude']
        lon = steps['longitude']
        self.leg_map.canvas.ax.plot(lon, lat, color='orchid',
                                    linewidth=1.5,
                                    transform=cartopy.crs.Geodetic())
        self.leg_map.canvas.draw()

    def verify_config(self):
        """Checks the config file director.ini

        The config file is read in during __init__, this verifies
        the correct formatting of the file. If new keys or values are
        added, this method needs to be updated.

        Raises
        ------
        ConfigError
            If any rules are violated
        """
        self.logger.info('Verifying config file')
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
            self.map_width = float(self.config['flight_map']['width'])
            self.marker_size = float(self.config['flight_map']['marker_size'])
            self.sample_rate = int(self.config['flight_map']['sample_rate'])
            self.update_freq = float(self.config['flight_map']['update_freq'])
        except ValueError:
            raise ConfigError('Unable to parse flight map settings.')

        self.logger.info('Configuration file passes')

    def popout_director_log(self):
        """Open the director log in separate window."""
        self.logger.info('Opened director log in popout window')
        DirectorLogDialog(self)

    def open_flight_map(self):
        """Open the flight map in popout window."""
        self.logger.info('Opened the flight map')
        FlightMap(self)

    def flag_file(self):
        """
        Update "BADCAL" flag for the selected row.

        When the "Flag File" on the Data Log tab is pressed, the "BADCAL" value
        for the selected row is set to "FLAG" in both the table and the
        background data structure.
        """
        row = self.table_data_log.currentRow()
        fname = self.data_filenames[row]
        self.logger.debug('Flagging bad calibration for %s' % fname)
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
            self.logger.info('Successful setup pane')
            self.logger.info('Flight plan: %s' % window.fname)
            # Parse the results of the dialog.
            if not window.fname:
                self.flight_plan_filename.setStyleSheet(self.warn_style)

            # Local timezone
            # Do this first so the flight plan times are parsed
            # with the correct timezone
            self.local_timezone = window.local_timezone
            self.localtz = pytz.timezone(self.local_timezone)
            self.logger.info('Timeszone set to {}'.format(self.localtz))

            # Parse the flight plan
            self.parse_flight_file(window.fname)
            #self.flight_info = window.flight_info

            # Instrument
            self.instrument = window.instrument
            self.instrument_text.setText(self.instrument)
            self.logger.info('Instrument set to {}'.format(self.instrument))
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
                self.txt_log_output_name.setStyleSheet(self.pass_style)
                self.logger.info('Director log output sent to {}'.format(
                    self.output_name))
            else:
                self.logger.warning('Director Log name not set')
                self.txt_log_output_name.setStyleSheet(self.fail_style)
                return

            # Location of data
            if window.data_dir:
                self.data_log_dir = window.data_dir
                self.txt_data_log_dir.setText('{0:s}'.format(
                    self.data_log_dir))
                # Select header checker rules
                self.choose_head_check_rules()
                self.logger.info('Data location set to {}'.format(self.data_log_dir))
            else:
                self.logger.warning('Data location not set')

            # Data Log filename
            if window.datalog_name:
                self.log_out_name = window.datalog_name
                self.txt_data_log_save_file.setText('{0:s}'.format(
                    os.path.basename(str(self.log_out_name))))
                self.txt_data_log_save_file.setStyleSheet(self.pass_style)
                self.logger.info('Data log output sent to {}'.format(
                    self.log_out_name))
            else:
                self.logger.warning('Data log output not set; Will not store data '
                                    'results')

            # Log append flags
            if window.append_data_log:
                # Check file exists
                if os.path.isfile(self.log_out_name):
                    self.data.add_images_from_log(self.log_out_name, self.headers)
                    self.update_table(append_init=True)
                    self.txt_data_log_save_file.setStyleSheet(self.pass_style)
                else:
                    self.logger.error('Data Log {} does not exist! Cannot '
                                      'append'.format(self.log_out_name))
                    self.txt_data_log_save_file.setText('{} does not '
                                                        'exist'.format(
                                                         self.log_out_name))
                    self.txt_data_log_save_file.setStyleSheet(self.fail_style)
            if window.append_director_log:
                # Check that file exists:
                if os.path.isfile(self.output_name):
                    self.read_director_log()
                    self.txt_log_output_name.setStyleSheet(self.pass_style)
                else:
                    self.logger.error('Director Log {} does not exist! Cannot '
                                      'append'.format(self.output_name))
                    self.txt_log_output_name.setText('{} does not '
                                                     'exist'.format(
                                                      self.output_name))
                    self.txt_log_output_name.setStyleSheet(self.fail_style)

    def choose_head_check_rules(self, data_file=None):
        """
        Selects the rules for checking header values.
        """
        if not data_file:
            self.logger.debug('Setting header checker rules, no data file provided')
            # Get a sample fits file from data directory
            config = self.config['search'][self.instrument]
            # Get the current list of FITS files in the location
            if config['method'] == 'glob':
                pattern = '{0:s}/*.{1:s}'.format(str(self.data_log_dir),
                                                 config['extension'])
                data_files = glob.glob(pattern)
                if data_files:
                    data_file = data_files[0]
                    self.logger.debug('Found data_file {} using glob'.format(
                        data_file))
                else:
                    self.checker_rules = None
                    self.logger.debug('Could not find a data file using glob')
                    return

            elif config['method'] == 'walk':
                pattern = '*.{0:s}'.format(config['extension'])
                for root, _, filenames in os.walk(str(self.data_log_dir)):
                    for filename in fnmatch.filter(filenames, pattern):
                        data_file = os.path.join(root, filename)
                        self.logger.debug('Found data file {} using walk'.format(
                            data_file))
                        break
                    break
            else:
                # Unknown method
                self.logger.warning('Unknown method {0:s} for instrument '
                                    '{1:s}'.format(config['method'],
                                                   self.instrument))
                self.checker_rules = None
                return

        self.logger.debug('Selecting header checking rules for {}'.format(data_file))
        # Pass it to self.checker.choose_rules
        rule = self.checker.choose_rules(data_file)
        self.logger.debug('Selected {}'.format(rule))

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
            self.logger.info('Starting full operations')
            # Start collecting data
            self.start_data_log = True
            # Start MET and TTL timers
            self.flight_timer('both')
            self.instrument_text.setText(self.instrument)
        else:
            self.txt_log_output_name.setStyleSheet(self.fail_style)

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
            self.logger.info('Ending program, begin writing logs')
            # Write the data log and director log one last time
            self.data.write_to_file(self.log_out_name, self.headers)
            self.logger.info('Data log written')
            self.write_director_log()
            self.logger.info('Director log written')
            # Close the app
            self.logger.info('Closing Cruise Director')
            self.close()

    def spawn_kw_window(self):
        """
        Opens the FITS Keywords select window.

        Called when the 'Edit Keywords...' button on the Data Log tab
        is pressed.
        """
        self.logger.debug('Opening keyword selector')
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
        """Updates the columns in the QTable Widget in the Data Log tab.

        Called initially when the window is first opened and again if the
        FITS keywords are changed. Due to the weird way the QtTableWidget
        works, the best way is to completely clear the table then remake it.
        """

        self.logger.debug('Updating data table columns in widget')
        # Clear the table
        self.table_data_log.setColumnCount(0)
        self.table_data_log.setRowCount(0)

        # Add the number of columns we'll need for the header keys given
        for _ in self.headers:
            col_position = self.table_data_log.columnCount()
            self.table_data_log.insertColumn(col_position)
        self.table_data_log.setHorizontalHeaderLabels(self.headers)

    def line_stamper(self, line):
        """Update the Cruise Director Log

        Appends a string given by line to the Director Log after
        it has been properly formatted by adding the UTC time and data
        stamp to the beginning. The line is added to both the GUI Log
        and the background list.

        Parameters
        ----------
        line : str
            The line to append to the log.
        """
        self.logger.debug('Appending to director log: {}'.format(line))

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
        """Write the cruise_log to file.

        Dumps the contents of the background list, cruise_log, to
        the file specified by output_name. If any error occurs,
        change the name of the output file on the GUI to an error
        message.
        """
        self.logger.debug('Writing director log to file')
        if self.output_name:
            try:
                with open(self.output_name, 'w') as f:
                    f.writelines(self.cruise_log)
            except IOError as e:
                self.logger.error('Cannot write director log to file:\n\t{}'.format(
                                  e))
                self.txt_log_output_name.setText('ERROR WRITING TO FILE!')

    def read_director_log(self):
        """Read in existing director log.

        Called if the user wants to append an existing director log
        to the new log.

        Raises
        ------
        IOError
            Raised if the existing log cannot be read in.
        """
        self.logger.info('Reading existing director log {}'.format(self.output_name))
        # Read in current log
        try:
            with open(self.output_name,'r') as f:
                existing_log = f.readlines()
        except IOError:
            message = ('Unable to read existing director log:\n'
                       '\t{0:s}'.format(self.output_name))
            raise IOError(message)

        self.logger.info('Read in {} lines from existing director log'.format(
                         len(existing_log)))
        # Add to current log
        for line in existing_log:
            self.cruise_log.append(line)
            self.log_display.append(line.strip())

    def mark_message(self, key):
        """Write a message to the director's log with timestamp.

        Parameters
        ----------
        key ; str
            Keyword to select which message will be posted. Options are:
             - mccs : notes a MCCS fault
             - si : notes a SI fault
             - land : landing
             - head : notes TO taking over
             - target : notes SI taking over
             - takeoff : takeoff
             - turn : notes turn off target
             - ignore : ignore last message
             - post : writes text user put in text box
        """

        self.logger.debug('Writing to director log with {} key'.format(key))
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

    def read_data_log(self):
        """
        Reads existing data log
        """
        pass

    def count_direction(self, key):
        """Set the direction the leg timer counts.

        Parameters
        ----------
        key : ['remain', 'elapse']
            Sets the leg timer to show remaining/elapsed time
        """
        self.logger.debug('Changing leg timer counting direction to {}'.format(key))
        if key == 'remain':
            # self.do_leg_count_elapsed = False
            self.leg_count_remaining = True
        elif key == 'elapse':
            # self.do_leg_count_elapsed = True
            self.leg_count_remaining = False
        else:
            return

    def set_date_time_edit_boxes(self):
        """Initialize the takeoff/landing fields.

        Initially sets the fields to the current time, so we don't have
        to type in as much. The fields will be overwritten if a flight
        plan is read in.
        """
        self.logger.debug('Initializing takeoff/landing time displays')
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
        """Start MET and/or TTL timers.

        Parameters
        ----------
        key : ['met', 'ttl', 'both']
            Specifies which timer to start.
        """
        self.logger.info('Starting flight timers.')
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
        """Determines the UTC/local time and fills the display strings.

        The  microseconds are zeroed outso everything will count
        together, otherwise it'll be out of sync due to microsecond
        delay between triggers/button presses. Called during
        initialization of the app and at the beginning of every show_lcd loop.
        """
        self.logger.debug('Updating time')
        self.utc_now = datetime.datetime.utcnow()
        self.utc_now = self.utc_now.replace(microsecond=0)
        self.utc_now_str = self.utc_now.strftime(' %H:%M:%S UTC')
        self.utc_now_datetime_str = self.utc_now.strftime('%m/%d/%Y %H:%M:%S $Z')

        # Safest way to sensibly go from UTC -> local timezone...?
        utc = pytz.utc.localize(self.utc_now)
        self.local_now = utc.astimezone(self.localtz)
        self.local_now_str = self.local_now.strftime(' %H:%M:%S %Z')
        self.local_now_datetime_str = self.local_now.strftime('%m/%d/%Y %H:%M:%S')

    def show_lcd(self):
        """The main loop for the code.

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
        if self.met_counting:
            self.logger.debug('Updating MET')
            # Set the MET to show the time between now and takeoff
            local2 = self.local_now.replace(tzinfo=None)
            takeoff2 = self.takeoff.replace(tzinfo=None)
            self.met = local2 - takeoff2
            self.met_str = '{0:s} MET'.format(total_sec_to_hms_str(self.met))
            self.txt_met.setText(self.met_str)
        if self.ttl_counting:
            self.logger.debug('Updating TTL')
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
                self.txt_ttl.setStyleSheet(self.pass_style)
            elif self.ttl.total_seconds() >= second_warning:
                self.txt_ttl.setStyleSheet(self.warn_style)
            else:
                self.txt_ttl.setStyleSheet(self.fail_style)

        if self.leg_timer.status == 'running':
            self.logger.debug('Update leg timers')
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

        self.plot_leg(self)

        # If the program is set to look for data automatically and the time
        # is a multiple of the update frequency and network is good
        if self.start_data_log and self.data_log_autoupdate.isChecked():
            if self.utc_now.second % self.data_log_update_interval.value() == 0:
                # If the network is good or if the user has turned off
                # checking the network
                if self.network_status or not self.network_status_control:
                    self.logger.debug('Check for data')
                    self.update_data()

    def manual_toggle_network(self):
        """Test button to toggle network status."""
        self.logger.info('Toggling test for network health.')
        if self.network_status_control:
            self.network_status_display_update()
            self.network_status_control = not self.network_status_control
        else: 
            self.network_status_display_update(stop=True)
            self.network_status_control = not self.network_status_control

    def verify_network(self, host='8.8.8.8', port=53, 
                       timeout=3, testing=False):
        """Test the current status of the network.

        Checks if Google can be pinged and if the data
        directory is still available. If not, set 
        good_connection flag low to pause data collection.
        """
        self.logger.debug('Testing network')
        if testing:
            self.network_status = not self.network_status
        elif self.network_status_hold:
            pass
        else:
            if self.file_check:
                if os.path.isdir(self.data_log_dir):
                    self.network_status = True
                else:
                    self.network_status = False
            else:
                self.network_status = False

    def network_status_display_update(self, stop=False):
        """Updates the GUI status with current network status."""
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
        """Set the color of the leg timer.

        Parameters
        ----------
        remaining_seconds : int
            Number of seconds left in the leg.
        """
        timer_warnings = self.config['leg_timer_minute_warnings']
        first_warning = float(timer_warnings['first'])*60
        second_warning = float(timer_warnings['second'])*60

        # Visual indicators setup
        if remaining_seconds >= first_warning:
            self.txt_leg_timer.setStyleSheet(self.pass_style)
        elif remaining_seconds >= second_warning:
            # Used to be orange. Maybe go back to this?
            self.txt_leg_timer.setStyleSheet(self.warn_style)
        else:
            self.txt_leg_timer.setStyleSheet(self.fail_style)

    def add_data_log_row(self):
        """Add a blank row to the Data Log.

        Called when the 'Add Blank Row' button in the Data
        Log tab is pressed.
        """

        self.logger.debug('Adding blank row to data log')
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
        """Removes a row from the Data Log.

        Called when the 'Remove Highlighted Row' button in
        the Data Log tab is pressed.
        """
        self.logger.info('Removing row from data log')
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
        """Recreate the data log table after keyword changes.

        This is called after changing keywords, blanks are filled,
        or a file has been flagged.
        """
        self.logger.info('Recreate data log')
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
        """Attempt to fill an empty cell in the QtTableWidget.

        If a cell in the data_log is empty after a change in
        keyword headers, read through the file headers again
        to see if the keyword is there.

        Parameters
        ----------
        n : int
            Index count of the file to process
        hkey : str
            Header keyword to fill in

        Returns
        -------
        val : str
            Value stored in the header ``hkey`` in selected file. If ``hkey``
            is not in the header, val is an empty string.
        """
        fname = self.data_filenames[n]

        try:
            val = '{0}'.format(self.data.header_vals[fname][hkey])
        except KeyError:
            val = ''
        self.logger.info('Filled missing value for key {0} in file {1} '
                         'with {2}'.format(hkey, fname, val))
        return val

    def update_data(self):
        """Look for new observations.

        Reads in new FITS files and adds them to the header_vals
        """

        self.logger.debug('Looking for new data')
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
            message = ('Unknown method {0:s} for instrument {1:s}'.format(
                       config['method'], self.instrument))
            self.logger.warning(message)
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
        self.logger.debug('Found {} new files'.format(len(new_files)))
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
        """Sort files based on method in config.

        Takes in the a list of files and sorts them. If there
        are problems return the unsorted list.

        Parameters
        ----------
        files : list
            List of files to be sorted.

        Returns
        -------
        files : list
            Same files but sorted according to config settings for
            the current instrument.
        """
        if self.config['sort'][self.instrument] == 'time':
            return sorted(files, key=os.path.getmtime)
        elif self.config['sort'][self.instrument] == 'name':
            if self.instrument.lower() == 'forcast':
                return sorted(files, key=lambda x:
                        int(os.path.basename(x).split('_')[-1].split('.')[0]))
                        #int(x.split(os.path.sep)[-1].split('_')[1].split('.')[0]))
            else:
                message = ('Unknown file formatting for {0:s} ',
                           'Cannot sort'.format(self.instrument))
                self.logger.warning(message)
                return files
        else:
            message = ('Unknown file sorting method. Check config file, '
                       'director.ini')
            self.logger.warning(message)
            return files

    def update_table(self, append_init=False):
        """Update the table widget to display newly found files."""

        self.logger.debug('Updating table widget')
        # Disable table features during alteration
        self.table_data_log.setSortingEnabled(False)
        self.table_data_log.horizontalHeader().setSectionsMovable(False)
        self.table_data_log.horizontalHeader().setDragEnabled(False)
        self.table_data_log.horizontalHeader().setDragDropMode(
            QtWidgets.QAbstractItemView.NoDragDrop)
        self.table_data_log.blockSignals(True)

        if append_init:
            self.logger.info('Updating table widget with data log '
                             'from a previous run')
            self.new_files = list(self.data.header_vals.keys())
            self.data_filenames = list(self.data.header_vals.keys())

        # Add the data to the table
        self.logger.debug('Added {} new files to table widget'.format(len(
                           self.new_files)))
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
        self.logger.debug('Done updated table widget')

    def leg_param_labels(self, key):
        """Toggle the visibility of the leg parameter labels.

        Parameters
        ----------
        key : ['on', 'off']
            Determines if the labels should be on or off
        """
        if key == 'on':
            self.logger.debug('Turn leg parameter labels on')
            self.txt_elevation.setVisible(True)
            self.txt_obs_plan.setVisible(True)
            self.txt_rof.setVisible(True)
            self.txt_target.setVisible(True)
        elif key == 'off':
            self.logger.debug('Turn leg parameter labels off')
            self.txt_elevation.setVisible(False)
            self.txt_obs_plan.setVisible(False)
            self.txt_rof.setVisible(False)
            self.txt_target.setVisible(False)
        else:
            return

    def toggle_leg_param_values_off(self):
        """Clear the leg parameter values.

        Useful for dead/departure/arrival legs
        """
        self.logger.debug('Turning off leg parameters')
        self.leg_elevation.setText('')
        self.leg_obs_block.setText('')
        self.leg_rof_rof_rate.setText('')
        self.leg_target.setText('')

    def update_leg_info_window(self):
        """Display details of flight plan parsed from .msi file."""
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
            self.logger.debug('Moving to leg {}'.format(self.leg_pos))

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
                    self.logger.exception('Exception during display of science leg '
                                          'information for leg '
                                          '{}'.format(self.leg_pos))
                    pass
            else:
                # If it's a dead leg, update the leg number and we'll move on
                # Clear values since they're probably crap
                self.logger.debug('Turning of leg info')
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
        """Move the leg position counter to the previous value."""
        if self.success_parse is True:
            self.leg_pos -= 1
            if self.leg_pos < 0:
                self.leg_pos = 0
            self.leg_info = self.flight_info.legs[self.leg_pos]
            self.logger.debug('Moving to previous leg, number {}'.format(
                self.leg_pos))
        self.update_leg_info_window()
        self.leg_timer.status = 'stopped'
        self.logger.debug('Stopped leg timer')
        self.setup_leg_map()

    def next_leg(self):
        """Move the leg position counter to the next value."""
        if self.success_parse is True:
            self.leg_pos += 1
            if self.leg_pos > self.flight_info.num_legs - 1:
                self.leg_pos = self.flight_info.num_legs - 1
            self.leg_info = self.flight_info.legs[self.leg_pos]
            self.logger.debug('Moved to next leg, number {}'.format(
                self.leg_pos))
        else:
            pass
        self.update_leg_info_window()
        self.leg_timer.status = 'stopped'
        self.logger.debug('Stopped leg timer')
        print('Updating map to {}'.format(self.leg_pos))
        self.setup_leg_map()

    def update_flight_time(self, key):
        """Fills the takeoff or landing time fields

        Grab the flight takeoff time from the flight plan, which is in UTC,
        and turn it into the time at the local location.
        Then, take that time and update the DateTimeEdit box in the GUI

        Parameters
        ----------
        key : ['takeoff', 'landing']
            Set if working with takeoff or landing leg
        """
        if key == 'takeoff':
            time = pytz.utc.localize(self.flight_info.takeoff)
        elif key == 'landing':
            time = self.flight_info.landing.replace(tzinfo=pytz.utc)
        else:
            return
        self.logger.debug('Updating flight time for {} leg'.format(key))
        time = time.astimezone(self.localtz)
        time_str = time.strftime('%m/%d/%Y %H:%M:%S')
        time_qt = QtCore.QDateTime.fromString(time_str, 'MM/dd/yyyy HH:mm:ss')
        if key == 'takeoff':
            self.takeoff_time.setDateTime(time_qt)
        else:
            self.landing_time.setDateTime(time_qt)

    def update_duration(self, reset=False):
        """Update the duration of the current leg.

        Parameters
        ----------
        reset : bool, optional
            Updates the duration of the current leg with user inputs,
            If reset is true, undo user changes and reset the duration to
            result from flight plan.
        """
        if reset:
            # Reset the duration to the current leg to
            # the duration from flight plan
            self.logger.debug('Resetting custom duration of leg number {} to '
                              'original value'.format(self.leg_pos))
            orig_duration = self.flight_info.legs[self.leg_pos].duration
            orig_duration = timedelta_to_time(orig_duration)
            self.leg_timer.control_timer('reset')
            self.leg_duration.setTime(orig_duration)
            self.txt_leg_duration.setText('Leg Duration')
        else:
            self.logger.debug('Changing duration of leg number {}'.format(
                self.leg_pos))
            new_duration = self.leg_duration.time().toPyTime()
            new_duration = datetime.timedelta(hours=new_duration.hour,
                                              minutes=new_duration.minute,
                                              seconds=new_duration.second)
            self.leg_timer.duration = new_duration
            self.txt_leg_duration.setText('Leg Duration (Changed)')

    def parse_flight_file(self, from_gui=None):
        """Parse flight plan from .msi file.

        Spawn the file chooser dialog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).
        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance

        Parameters
        ----------
        from_gui : str, optional
            Name of the flight plan to parse, defaults to None which prompts user
            for the flight plan's file name.
        """
        # If from_gui is None, prompt the user to select a filename
        if not from_gui:
            self.fname = ''
        else:
            self.fname = from_gui
        self.logger.debug('Parsing flight plan: {}'.format(self.fname))
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
        self.flight_plan_filename.setStyleSheet(self.pass_style)
        self.flight_plan_filename.setText(os.path.basename(str(self.fname)))
        try:
            self.flight_info = fpmis.parse_mis_file(self.fname)
            self.leg_info = self.flight_info.legs[self.leg_pos]
            self.success_parse = True
            self.update_leg_info_window()
            if self.set_takeoff_fp.isChecked() is True:
                self.update_flight_time('takeoff')
            if self.set_landing_fp.isChecked() is True:
                self.update_flight_time('landing')
            self.logger.debug('Flight plan successfully parsed.')
        except IOError:
            self.flight_info = ''
            self.err_msg = 'ERROR: Failure Parsing File!'
            self.flight_plan_filename.setStyleSheet(self.fail_style)
            self.flight_plan_filename.setText(self.err_msg)
            self.success_parse = False
            self.logger.exception('Failure while parsing {}'.format(self.fname))


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


def timedelta_to_time(delta):
    """Converts a timedelta object to a time object"""
    hours = delta.seconds/3600.
    ihours = np.int(hours)
    minutes = (hours - ihours) *60
    iminutes = np.int(minutes)
    seconds = (minutes - iminutes) * 60.
    iseconds = np.int(seconds)
    t = datetime.time(hour=ihours, minute=iminutes, second=iseconds)
    return t


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

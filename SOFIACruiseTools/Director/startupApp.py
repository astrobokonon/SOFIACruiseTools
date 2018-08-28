
import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

import SOFIACruiseTools.support.mis_parser as fpmis
import SOFIACruiseTools.Director.directorStartupDialog as ds

from SOFIACruiseTools.Director.FITSKeyWordDialog import FITSKeyWordDialog


class StartupApp(QtWidgets.QDialog, ds.Ui_Dialog):
    """
    GUI to configure run of Cruise Director
    """
    def __init__(self, parent=None):

        super(StartupApp, self).__init__(parent)

        self.setupUi(self)

        self.config = self.parentWidget().config

        # Grab stuff from parent
        self.utc_now = self.parent().utc_now
        self.fits_hdu = self.parentWidget().fits_hdu
        self.required_fields = self.parent().required_fields

        # Testing button
        self.test_config.clicked.connect(self.load_default)

        self.flightButton.clicked.connect(self.load_flight)
        self.instSelect.activated.connect(self.select_instr)
        self.logOutButton.clicked.connect(self.select_log_file)
        self.datalocButton.clicked.connect(self.select_data_loc)
        self.datalogButton.clicked.connect(self.select_data_log)
        self.fitkwButton.clicked.connect(self.select_kw)
        self.fitkwButton.setText('Change')
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.accepted.connect(self.start)
        self.timezoneSelect.activated.connect(self.select_local_timezone)
#        self.appendCheck.clicked.connect(self.append_options)

        self.local_timezone = str(self.timezoneSelect.currentText())
        self.instrument = str(self.instSelect.currentText())
        if 'hawc' in self.instrument.lower():
            self.instrument = 'HAWC'
#        if 'flight' in self.instrument.lower():
#            self.instrument = 'HAWCFLIGHT'
#        elif 'ground' in self.instrument.lower():
#            self.instrument = 'HAWCGROUND'
        self.select_kw(default=1)

        if self.parentWidget().log_out_name:
            self.dirlog_name = self.parentWidget().log_out_name
            self.logOutText.setText(self.dirlog_name)
        else:
            self.dirlog_name = ''

        if self.parentWidget().data_log_dir:
            self.data_dir = self.parentWidget().data_log_dir
            self.datalocText.setText(self.data_dir)
        else:
            self.data_dir = ''

        if self.parentWidget().output_name:
            self.datalog_name = self.parentWidget().output_name
            self.datalogText.setText(self.datalog_name)
        else:
            self.datalog_name = ''

        if self.parentWidget().fname:
            self.fname = self.parentWidget().fname
            self.flightText.setText(self.fname)
        else:
            self.fname = ''

        if self.parentWidget().headers:
            self.headers = self.parentWidget().headers
        else:
            self.headers = self.config['keywords'][self.instrument]

        if self.parentWidget().local_timezone != 'US/Pacific':
            self.local_timezone = self.parentWidget().local_timezone
            tz_index = self.timezoneSelect.findText(self.local_timezone,
                                                    QtCore.Qt.MatchFixedString)
            if tz_index > 0:
                self.timezoneSelect.setCurrentIndex(tz_index)

        self.err_msg = ''
        self.flight_info = None
        self.success_parse = False
        self.append_data_log = False
        self.append_director_log = False

    def append_options(self):
        """ Flag to choose if logs should be appended to or overwritten """
        self.append_option = True

    def load_default(self):
        """ Loads default settings for faster testing. """
        self.instrument = 'FIFI-LS'
        self.local_timezone = 'US/Pacific'
        code_dir = os.path.dirname(os.path.realpath(__file__))
        #flight_file = f'{code_dir}/../../inputs/201803_FI_DIANA_SCI.mis'
        flight_file = '{0:s}/../../inputs/201803_FI_DIANA_SCI.mis'.format(code_dir)
        #print(f'Loading flight plan: {flight_file}')
        print('Loading flight plan: {0:s}'.format(flight_file))
        self.load_flight(fname = flight_file)
        #print(f'Successful Parse: {self.success_parse}')
        print('Successful Parse: {}'.format(self.success_parse))
        timestamp = self.utc_now.strftime('%Y%m%d.txt')
        #self.dirlog_name = f'SILog_{timestamp}'
        #self.datalog_name = f'DataLog_{timestamp}'
        self.dirlog_name = 'SILog_{0:s}'.format(timestamp)
        self.datalog_name = 'DataLog_{0:s}'.format(timestamp)
        self.data_dir = '/home/jrvander/mounts/preview/misc/JV_tmp/cruiseFiles/'

    def start(self):
        """
        Closes this window and passes results to main program
        """
        # Read the timezone
        self.local_timezone = str(self.timezoneSelect.currentText())

        # Check the append check
        self.append_data_log = self.appendDataCheck.checkState()>0
        self.append_director_log = self.appendLogCheck.checkState()>0

        # Read the instrument selection
        self.instrument = str(self.instSelect.currentText())
        if 'hawc' in self.instrument.lower():
            self.instrument = 'HAWC'
#            if 'flight' in self.instrument.lower():
#                self.instrument = 'HAWCFLIGHT'
#            elif 'ground' in self.instrument.lower():
#                self.instrument = 'HAWCGROUND'
        self.close()

    def load_flight(self, fname=None):
        """
        Parses flight plan from .msi file.

        Spawn the file chooser diaglog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).
        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance.
        """
        if fname:
            self.fname = fname
        else:
            self.fname = QtWidgets.QFileDialog.getOpenFileName()[0]
        if self.fname:
            # Make sure the label text is black every time we start, and
            # cut out the path so we just have the filename instead of huge str
            self.flightText.setStyleSheet('QLabel { color : black; }')
            self.flightText.setText(os.path.basename(str(self.fname)))
            try:
                # self.flight_info = fpmis.parseMIS(self.fname)
                self.flight_info = fpmis.parse_mis_file(self.fname)
                self.success_parse = True
                self.flightButton.setText('Change')
                inst_index = self.instSelect.findText(self.flight_info.instrument,
                                                      QtCore.Qt.MatchFixedString)
                if inst_index > 0:
                    self.instSelect.setCurrentIndex(inst_index)
            except (IOError, IndexError, AttributeError) as e:
                print(e)
                self.flight_info = ''
                self.err_msg = 'ERROR: Failure Parsing {0:s}!'.format(
                                os.path.basename(self.fname))
                self.flightText.setStyleSheet('QLabel { color : red; }')
                self.flightText.setText(self.err_msg)
                self.success_parse = False

    def select_instr(self):
        """
        Selects the instrument
        """
        self.instrument = str(self.instSelect.currentText())
        if 'hawc' in self.instrument.lower():
            self.instrument = 'HAWC'
#        if 'Flight' in self.instrument:
#            self.instrument = 'HAWCFLIGHT'
#        elif 'Ground' in self.instrument:
#            self.instrument = 'HAWCGROUND'

    def select_local_timezone(self):
        """
        Sets the local timezone
        """
        self.local_timezone = str(self.timezoneSelect.currentText())

    def select_log_file(self):
        """
        Selects the output file for the director log
        """
        default = 'SILog_{0:s}'.format(self.utc_now.strftime('%Y%m%d.txt'))
        if self.datalog_name:
            directory = os.path.join(os.path.dirname(self.datalog_name), default)
        else:
            directory = default
        self.dirlog_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                 'Save File',
                                                                 directory)[0]
        if self.dirlog_name:
            self.logOutText.setText('{0:s}'.format(os.path.basename(
                                                   str(self.dirlog_name))))
            self.logOutButton.setText('Change')

    def select_data_loc(self):
        """
        Sets where to look for data files
        """
        dtxt = 'Select Data Directory'
        self.data_dir = QtWidgets.QFileDialog.getExistingDirectory(self, dtxt)
        # If instrument is set to FORCAST, then check for r/b subdirectories
        if self.data_dir:
            if self.instrument.lower() == 'forcast':
                r_subdir = os.path.join(self.data_dir, 'r')
                b_subdir = os.path.join(self.data_dir, 'b')
                if not os.path.isdir(r_subdir) or not os.path.isdir(b_subdir):
                    print('WARNING: Data Location not properly configured '
                          'for FORCAST! Need r and/or b subdirectories '
                          'in the Data Location!')
            self.datalocText.setText(self.data_dir)
            self.datalocButton.setText('Change')

    def select_data_log(self):
        """
        Selects where to store the data log
        """
        default = 'DataLog_{0:s}'.format(self.utc_now.strftime('%Y%m%d.csv'))
        print('Selecting datalog name')
        if self.dirlog_name:
            directory = os.path.join(os.path.dirname(self.dirlog_name), default)
        else:
            directory = default
        self.datalog_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                  'Save File',
                                                                  directory,
                                                                  #default,
                                                                  #directory=directory
                                                                  )[0]
#        self.datalog_name = QtWidgets.QFileDialog.getOpenFileName(self,
#                                                                  'Open File',
#                                                                  default)[0]
        if os.path.isfile(self.datalog_name):
            with open(self.datalog_name,'r') as f:
                print('Length of existing data log: ',len(f.readlines()))
            print('Datalog Name: ',self.datalog_name)

        if self.datalog_name:
            self.datalogText.setText(
                '{0:s}'.format(os.path.basename(str(self.datalog_name))))
            self.logOutButton.setText('Change')

    def select_kw(self, default=None):
        """
        Selects what FITS keywords to use
        """

        # Read the default keywords for each instrument
        self.headers = self.config['keywords'][self.instrument]
        for i, require in enumerate(self.required_fields):
            if require not in self.headers:
                self.headers.insert(i, require)

        if not default:
            window = FITSKeyWordDialog(self)
            result = window.exec_()
            if result == 1:
                self.fits_hdu = np.int(window.fitskw_hdu.value())
                self.headers = window.headers
                for i, require in enumerate(self.required_fields):
                    if require not in self.headers:
                        self.headers.insert(i, require)
                self.fitskwText.setText('Custom')

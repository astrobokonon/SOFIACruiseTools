
from __future__ import print_function,division,absolute_import
import pytz
import glob
import fnmatch
import sys
import datetime
from os.path import basename
from configobj import ConfigObj
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from . import directorStartup as ds
#import directorStartup as ds
from .. import support as fpmis
from . import SOFIACruiseDirector as scd

class startupApp(QtWidgets.QMainWindow, ds.Ui_MainWindow):
    def __init__(self):

        super(self.__class__,self).__init__()
    
        self.setupUi(self)

        self.flightButton.clicked.connect(self.load_flight)
        self.instSelect.activated.connect(self.select_instr)
        self.logOutButton.clicked.connect(self.select_log_file)
        self.datalocButton.clicked.connect(self.select_data_loc)
        self.datalogButton.clicked.connect(self.select_data_log)
        self.fitkwButton.clicked.connect(self.select_kw)
        self.startButton.clicked.connect(self.start)

        self.instrument = str(self.instSelect.currentText())
        if 'HAWC' in self.instrument:
            self.instrument = 'HAWC'
        self.dirlog_name = ''
        self.data_dir = ''
        self.datalog_name = ''
        self.utc_now = datetime.datetime.utcnow()

    def start(self):
        """
        Closes this window and passes results to main program
        """

        # Read the instrument selection
        self.instrument = str(self.instSelect.currentText())
        if 'HAWC' in self.instrument:
            self.instrument = 'HAWCFLIGHT'
        self.close()

    def load_flight(self):
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
        self.flightText.setStyleSheet('QLabel { color : black; }')
        self.flightText.setText(basename(str(self.fname)))
        try:
            self.flight_info = fpmis.parseMIS(self.fname)
            self.success_parse = True
            index = self.instSelect.findText(self.flight_info.instrument,
                                            QtCore.Qt.MatchFixedString)
            if index >= 0: 
                self.instSelect.setCurrentIndex(index)
        except IOError:
            self.flight_info = ''
            self.err_msg = 'ERROR: Failure Parsing File!'
            self.flightText.setStyleSheet('QLabel { color : red; }')
            self.flightText.setText(self.err_msg)
            self.success_parse = False

    def select_instr(self):
        """
        Selects the instrument
        """
        self.instrument = str(self.instSelect.currentText())
        if 'HAWC' in self.instrument:
            self.instrument = 'HAWC'

    def select_log_file(self):
        """
        Selects the output file for the director log
        """
        
        default = 'SILog_{0:s}'.format(self.utc_now.strftime('%Y%m%d.txt'))
        self.dirlog_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                'Save File',default)[0]
        if self.dirlog_name:
            self.logOutText.setText('{0:s}'.format(basename(str(self.dirlog_name))))

    def select_data_loc(self):
        """
        Sets where to look for data files
        """
        
        dtxt = 'Select Data Directory'
        self.data_dir = QtWidgets.QFileDialog.getExistingDirectory(self,dtxt)
        
        if self.data_dir:
            self.datalocText.setText(self.data_dir)

 
    def select_data_log(self):
        """
        Selects where to store the data log
        """
        default = 'DataLog_{0:s}'.format(self.utc_now.strftime('%Y%m%d.txt'))
        self.datalog_name = QtWidgets.QFileDialog.getSaveFileName(self,
                                'Save File',default)[0]
        if self.datalog_name:
            self.datalogText.setText('{0:s}'.format(basename(str(self.datalog_name))))

    def select_kw(self):
        """
        Selects what FITS keywords to use
        """
        print('Selecting FITS keywords')

        # Read the default keywords for each instrument
        fname = 'director.ini'
        config = ConfigObj(fname)
        self.headers = config['keywords'][self.instrument.lower()]
    
        self.fits_hdu = 0
        window = scd.FITSKeyWordDialog(self)
        result = window.exec_()
        if result == 1:
            self.fits_hdu = np.int(window.fitskw_hdu.value())
            self.headers = window.headers
            if 'NOTES' not in self.headers:
                self.headers.insert(0,'NOTES')
            self.fitskwText.setText('Custom')
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    form = startupApp()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()


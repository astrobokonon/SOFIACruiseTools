"""
Created on Thu Jun 15 11:20:07 2017

@author: rhamilton
"""

from __future__ import division, print_function

import sys
from os.path import basename

import numpy as np
import astropy.table as apt
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, \
    QAbstractItemView, QTableWidgetItem

import MainWindow as scpp
import SOFIACruiseTools.support.newparse as fpmis


def scrapeMIS(filename):
    flightInfo = fpmis.parseMIS(filename)
    # Note that this will grab the table of JUST the
    #   takeoff, observing, and landing leg details
    obstab = []
    obstabhed = []
    for j, oach in enumerate(flightInfo.legs):
        if oach.legtype != "Observing":
            oach.ra = None
            oach.dec = None
            oach.range_rof = [None, None]
            oach.range_elev = [None, None]
            oach.range_rofrt = [None, None]
            oach.range_thdgrt = [None, None]

        # print the header before the first leg
        if j == 0:
            obstabhed = ["Leg Number",
                         "Time Since Takeoff at Leg Start (hrs)",
                         "Leg Type", "ObsBlk", "Target",
                         "RA (2000)", "Dec (2000)",
                         "Obs Duration",
                         "Elevation Range",
                         "ROF Range",
                         "ROF Rate", "THdg Rate"]

            # Should be self explanatory here
        if oach.legtype == "Takeoff" or oach.legtype == "Landing" or\
          oach.legtype == "Observing":
            tabdat = [oach.legno,
                      np.round(oach.relative_time[0]/60./60., 1),
                      oach.legtype, oach.obsblk,
                      oach.target, oach.ra, oach.dec,
                      str(oach.obsdur),
                      str(oach.range_elev)[1:-1],
                      str(oach.range_rof)[1:-1],
                      str(oach.range_rofrt)[1:-1],
                      str(oach.range_thdgrt)[1:-1]]

            obstab.append(tabdat)
    # Pack it into an easier-to-interact-with table object
    dataFlight = apt.Table(rows=obstab, names=obstabhed)

    return flightInfo, dataFlight


class SOFIACruisePlannerApp(QMainWindow, scpp.Ui_MainWindow):
    def __init__(self):
        # Since the SOFIACruiseDirectorPanel file will be overwritten each time
        #   we change something in the design and recreate it, we will not be
        #   writing any code in it, instead we'll create a new class to
        #   combine with the design code
        super(self.__class__, self).__init__()
        # This is defined in SOFIACruiseDirectorPanel.py file automatically;
        #   It sets up layout and widgets that are defined, and then shows it
        self.setupUi(self)

        # Setting some states
        self.tableFlightPlanSummary.setSortingEnabled(False)
        self.tableFlightPlanSummary.horizontalHeader().setDragEnabled(False)
        self.tableFlightPlanSummary.horizontalHeader().setDragDropMode(QAbstractItemView.NoDragDrop)

        self.comboBoxInstruments.addItems(['EXES', 'FIFI-LS', 'FLITECAM',
                                           'FORCAST', 'FPI+', 'GREAT',
                                           'HAWC+', 'HIPO', 'HIRMES'])
        self.comboBoxInstruments.setCurrentIndex(6)

        # Hooking up the menu options and buttons to their actions
        self.actionOpen_Flight_Plan.triggered.connect(self.selectInputFlight)
#        self.actionChoose_Flight_Plan_Image.triggered.connect(self.selectInputFile)

        # Flight plan progression
        self.buttonPreviousLeg.clicked.connect(self.prevLeg)
        self.buttonNextLeg.clicked.connect(self.nextLeg)

    def setFlightTableData(self):
        """
        Given a parsed flight plan, put the flight information into a nice
        table view to allow the user to easily see stuff
        """
        # Create the data table items and populate things

        # Update with the new number of colums
        self.tableFlightPlanSummary.setColumnCount(len(self.dataFlight.colnames[1:]))
        self.tableFlightPlanSummary.setHorizontalHeaderLabels(self.dataFlight.colnames[1:])

        nrowlabels = []
        for n, row in enumerate(self.dataFlight):
            self.tableFlightPlanSummary.insertRow(n)
            lab = "Leg %02i" % (self.dataFlight["Leg Number"][n])
            nrowlabels.append(lab)
            for m, hkey in enumerate(self.dataFlight.colnames[1:]):
                newitem = QTableWidgetItem(str(row[hkey]))
                self.tableFlightPlanSummary.setItem(n, m, newitem)

        self.tableFlightPlanSummary.setVerticalHeaderLabels(nrowlabels)

        # Resize to minimum required, then display
        self.tableFlightPlanSummary.resizeColumnsToContents()
        self.tableFlightPlanSummary.resizeRowsToContents()

        self.tableFlightPlanSummary.show()

    def selectInputFlight(self):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).

        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance
        """
        self.fname = QFileDialog.getOpenFileName()[0]
        print(self.fname)
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
        self.labelFlightPlanFilename.setStyleSheet("QLabel { color : black; }")
        self.labelFlightPlanFilename.setText(basename(str(self.fname)))
        try:
            self.flightinfo, self.dataFlight = scrapeMIS(self.fname)

            # If that worked, make sure the table is cleared then update
            self.tableFlightPlanSummary.setRowCount(0)
            self.tableFlightPlanSummary.setColumnCount(0)
            self.setFlightTableData()
            self.successparse = True
        except Exception as err:
            print(str(err))
            self.flightinfo = ''
            self.errmsg = 'ERROR: Failure Parsing File!'
            self.labelFlightPlanFilename.setStyleSheet("QLabel { color : red; }")
            self.labelFlightPlanFilename.setText(self.errmsg)
            self.successparse = False

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


def main():
    app = QApplication(sys.argv)
#    QtGui.QFontDatabase.addApplicationFont("resources/fonts/digital_7/digital-7_mono.ttf")
    form = SOFIACruisePlannerApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()

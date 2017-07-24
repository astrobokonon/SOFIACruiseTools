"""
Created on Thu Jun 15 11:20:07 2017

@author: rhamilton
"""

from __future__ import division, print_function, absolute_import

import sys
import getpass
from os.path import basename

import numpy as np
import astropy.table as apt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, \
    QHeaderView, QTableWidgetItem

from . import mainwindow as panel
from .. import support as fpmis


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


class SOFIACruiseReviewerApp(QMainWindow, panel.Ui_MainWindow):
    def __init__(self):
        # Since the ...Panel file will be overwritten each time
        #   we change something in the design and recreate it, we will not be
        #   writing any code in it, instead we'll create a new class to
        #   combine with the design code
        super(self.__class__, self).__init__()
        # This is defined in ...Panel.py file automatically;
        #   It sets up layout and widgets that are defined, and then shows it
        self.setupUi(self)

        # Setting some states
        self.flightbasics = {}
        self.listoflights = []
        self.newflights = []

        # I think this is cross-platform?  I guess we'll see
        self.lineEditUserName.setText(getpass.getuser())

        # Hooking up the menu options and buttons to their actions
        self.pushButtonAddFlight.clicked.connect(self.addFlightToList)
        self.pushButtonRemoveFlight.clicked.connect(self.removeFlightFromList)

        # If something is typed in either of these boxes, update the class
        self.lineEditSeriesTitle.editingFinished.connect(self.setSeriesTitle)
        self.lineEditUserName.editingFinished.connect(self.setUserName)

        # Need this to catch the dragged signal in the series overview table
        self.flightBasicsModel = self.tableWidgetFlightBasics.model()
        self.flightBasicsModel.rowsMoved.connect(self.reorderFlightList)

        # Custom signal that gets emitted in the drop method of DragDropTable
        self.tableWidgetFlightBasics.rearranged.connect(self.reorderFlightList)

        # Click to change to the details for that flight
        self.tableWidgetFlightBasics.clicked.connect(self.selectFlight)

        # Generate a list of the available signals
        metaobject = self.tableWidgetFlightBasics.metaObject()
        for i in range(metaobject.methodCount()):
            mobm = metaobject.method(i)
            print(mobm.methodSignature())

        # Create the review class
        self.seReview = fpmis.seriesreview()
        self.setSeriesTitle()
        self.setUserName()

        # Flight plan progression
#        self.buttonPreviousLeg.clicked.connect(self.prevLeg)
#        self.buttonNextLeg.clicked.connect(self.nextLeg)

    def selectFlight(self):
        # The TableWidget is set with row selection only, so this will always
        #   have length = 1 (but still is a list)
        sel = self.tableWidgetFlightBasics.selectionModel().selectedRows()[0]
        sel = sel.row()
#        print("%s" % self.seReview.flights[sel].

    def setUserName(self):
        """
        """
        self.seReview.reviewername = self.lineEditUserName.text()

    def setSeriesTitle(self):
        """
        """
        self.seReview.seriesname = self.lineEditSeriesTitle.text()

    def parseFlightList(self):
        """
        Given a list of filenames, attempt to parse each one
        and fill a class holding them all.

        When done, fill in a table giving the vital statistics of each.

        The class (seriesreview in MISparse) is a nested framework.
        Go look there.
        """
        # Clear out the old crud
        self.seReview.flights = []
        self.tableWidgetFlightBasics.setRowCount(0)
        labs = ['Fancy Name', 'Takeoff', 'Duration',
                'Obs. Time', 'Airports']
        self.tableWidgetFlightBasics.setColumnCount(len(labs))
        self.tableWidgetFlightBasics.setHorizontalHeaderLabels(labs)

        for i, each in enumerate(self.listoflights):
            print("Parsing %s ..." % each, end=' ')
            bname = basename(each)
            fdict = {}
            try:
                cflight = fpmis.parseMIS(each)
                self.seReview.flights.append(cflight)
                print("Success!")

                # Now fill in the table
                fdict['Filename'] = bname
                fdict['Fancy Name'] = cflight.fancyname
                fdict['Takeoff'] = str(cflight.takeoff).split(" ")[0]
                fdict['Duration'] = str(cflight.flighttime)
                fdict['Obs. Time'] = str(cflight.obstime)
                dstr = "%s to %s" % (cflight.origin, cflight.destination)
                fdict['Airports'] = dstr
            except:
                print("Failed to parse %s" % each)
                # Fill out the table
                for key in labs:
                    if key == 'Filename':
                        fdict[key] = bname
                    else:
                        fdict[key] = ''
            self.flightbasics[bname] = fdict

            # Now actually fill the table widget
            self.tableWidgetFlightBasics.insertRow(i)
            for j, hkey in enumerate(labs):
                newitem = QTableWidgetItem(str(fdict[hkey]))
                newitem.setTextAlignment(Qt.AlignCenter)
                self.tableWidgetFlightBasics.setItem(i, j, newitem)
            self.tableWidgetFlightBasics.item(i, 0).setToolTip(each)

        # Resize before displaying
        self.tableWidgetFlightBasics.resizeRowsToContents()
        hhead = self.tableWidgetFlightBasics.horizontalHeader()
        hhead.setSectionResizeMode(QHeaderView.Stretch)

    def addFlightToList(self):
        tstr = "Load SOFIA Flight Plan"
        filt = "MIS (*.mis);;FSR (*.fsr)"
        self.newflights = QFileDialog.getOpenFileNames(self,
                                                       tstr,
                                                       filt)[0]

        # Make sure it's flat so it's trivial to itterate over
        for thingy in self.newflights:
            self.listoflights.append(thingy)

        print("Full list with newly added things:")
        print(self.listoflights)
        print("=====")

        # Need to only update what is needed.
        self.parseFlightList()

    def removeFlightFromList(self):
        bad = self.tableWidgetFlightBasics.currentRow()
        if bad != -1:
            self.tableWidgetFlightBasics.removeRow(bad)

        self.updateFlightList()

    def updateFlightList(self):
        """
        Re-set the internal listoflights property from the current
        contents of the listWidgetFlights box in the panel
        """
        self.listoflights = []
        print("I see %i items" % self.tableWidgetFlightBasics.rowCount())
        for j in range(self.tableWidgetFlightBasics.rowCount()):
            floc = self.tableWidgetFlightBasics.item(j, 0).toolTip()
            self.listoflights.append(floc)
            print(floc)
#        print("Updated internal list:")
#        print(self.listoflights)
        self.parseFlightList()

    def reorderFlightList(self):
        self.updateFlightList()
        print(self.listoflights)

    def setFlightTableData(self):
        """
        Given a parsed flight plan, put the flight information into a nice
        table view to allow the user to easily see stuff
        """
        # Create the data table items and populate things

        # Update with the new number of colums
        self.tableViewCurrentFlight.setColumnCount(len(self.dataFlight.colnames[1:]))
        self.tableViewCurrentFlight.setHorizontalHeaderLabels(self.dataFlight.colnames[1:])

        nrowlabels = []
        for n, row in enumerate(self.dataFlight):
            self.tableViewCurrentFlight.insertRow(n)
            lab = "Leg %02i" % (self.dataFlight["Leg Number"][n])
            nrowlabels.append(lab)
            for m, hkey in enumerate(self.dataFlight.colnames[1:]):
                newitem = QTableWidgetItem(str(row[hkey]))
                self.tableViewCurrentFlight.setItem(n, m, newitem)

        self.tableViewCurrentFlight.setVerticalHeaderLabels(nrowlabels)

        # Resize to minimum required, then display
        self.tableViewCurrentFlight.resizeColumnsToContents()
        self.tableViewCurrentFlight.resizeRowsToContents()

        self.tableViewCurrentFlight.show()

    def selectInputFlight(self):
        """
        Spawn the file chooser diaglog box and return the result, attempting
        to parse the file as a SOFIA flight plan (.mis).

        If successful, set the various state parameters for further use.
        If unsuccessful, make the label text red and angry and give the
        user another chance
        """
        self.fnames = QFileDialog.getOpenFileName()

        self.basedFnames = []
        for each in self.fnames:
            self.basedFnames.append(basename(each))
        # Make sure the label text is black every time we start, and
        #   cut out the path so we just have the filename instead of huge str
#        self.labelCurrentFlight.setStyleSheet("QLabel { color : black; }")
#        self.labelCurrentFlight.setText(basename(str(self.fname)))
        try:
            # Need to impliment new classes starting to be populated here!
            self.flightinfo, self.dataFlight = scrapeMIS(each)

            # If that worked, make sure the table is cleared then update
            self.tableViewCurrentFlight.setRowCount(0)
            self.tableViewCurrentFlight.setColumnCount(0)
            self.setFlightTableData()
        except Exception as err:
            print(str(err))
            self.flightinfo = ''
            self.errmsg = 'ERROR: Failure Parsing File!'
            self.labelCurrentFlight.setStyleSheet("QLabel { color : red; }")
            self.labelCurrentFlight.setText(self.errmsg)
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
    form = SOFIACruiseReviewerApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()

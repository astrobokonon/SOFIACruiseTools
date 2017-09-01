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

        # Custom signal that gets emitted in the drop method of DragDropTable
        self.tableWidgetFlightBasics.rearranged.connect(self.updateFlightList)

        # Click to change to the details for that flight
        self.tableWidgetFlightBasics.clicked.connect(self.selectFlight)
        
        # Autoreview/clear review
        self.pushButtonAutoReview.clicked.connect(self.autoReviewSelected)
        
        # Catch events from plainTextEdit boxes being changed by the user
        #
        # NOTE: This signal sucks and triggers on each and every character
        #
        self.plainTextEditWarnings.textChanged.connect(self.updateCommentBoxes)

        # Generate a list of the available signals
        metaobject = self.plainTextEditNotes.metaObject()
        for i in range(metaobject.methodCount()):
            mobm = metaobject.method(i)
            print(mobm.methodSignature())

        # Create the review class
        self.seReview = fpmis.seriesreview()
        self.seReview.flights = {}
        self.setSeriesTitle()
        self.setUserName()

    def updateCommentBoxes(self):
        print("Box updated!")
        pass

    def autoReviewSelected(self):
        # The TableWidget is set with row selection only, so this will always
        #   have length = 1 (but still is a list)
        sel = self.tableWidgetFlightBasics.selectionModel().selectedRows()[0]
        sel = sel.row()
        # Get the hash of the selected file
        selHash = self.tableWidgetFlightBasics.item(sel, 1).toolTip()
        print("Row %i selected, file has hash %s" % (sel, selHash))
        
        coms = fpmis.autoReview(self.seReview.flights[selHash])
        self.seReview.flights[selHash].reviewComments = coms
        print(coms)        

        # Now fill out the text boxes with the contents of the auto review
        self.fillReviewBoxes()

    def fillReviewBoxes(self):
        # Clear the boxes of their former contents
        self.plainTextEditNotes.clear()
        self.plainTextEditWarnings.clear()
        self.plainTextEditErrors.clear()
        self.plainTextEditTips.clear()
        
        # The TableWidget is set with row selection only, so this will always
        #   have length = 1 (but still is a list)
        sel = self.tableWidgetFlightBasics.selectionModel().selectedRows()[0]
        sel = sel.row()
        # Get the hash of the selected file
        selHash = self.tableWidgetFlightBasics.item(sel, 1).toolTip()
        print("Row %i selected, file has hash %s" % (sel, selHash))
        
        # Notes
        for each in self.seReview.flights[selHash].reviewComments.notes:
            self.plainTextEditNotes.appendPlainText(each)
        
        # Warnings
        for each in self.seReview.flights[selHash].reviewComments.warnings:
            self.plainTextEditWarnings.appendPlainText(each)
                    
        # Errors
        for each in self.seReview.flights[selHash].reviewComments.errors:
            self.plainTextEditErrors.appendPlainText(each)
        
        # Tips
        for each in self.seReview.flights[selHash].reviewComments.tips:
            self.plainTextEditTips.appendPlainText(each)

    def selectFlight(self):
        # The TableWidget is set with row selection only, so this will always
        #   have length = 1 (but still is a list)
        sel = self.tableWidgetFlightBasics.selectionModel().selectedRows()[0]
        sel = sel.row()
        # Get the hash of the selected file
        selHash = self.tableWidgetFlightBasics.item(sel, 1).toolTip()
        print("Row %i selected, file has hash %s" % (sel, selHash))

        # Update the label of the bottom section
        self.labelCurrentFlight.setText(self.seReview.flights[selHash].filename)
        
        # Note that this will grab the table of JUST the
        #   takeoff, observing, and landing leg details
        obstab = []
        obstabhed = []
        flightInfo = self.seReview.flights[selHash]
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
                             "Time Since Takeoff (hrs)",
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
        self.dataFlight = apt.Table(rows=obstab, names=obstabhed)
        
        self.setFlightTableData()
        self.fillReviewBoxes()

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
        # Save the old contents since we may have parsed some stuff or 
        #   commented on some stuff already
        oldFlights = self.seReview.flights
        oldHashes = oldFlights.keys()

        # Create a new fresh dict
        self.seReview.flights = {}

        self.tableWidgetFlightBasics.setRowCount(0)
        # Note the order here is the order it'll show in the table
        labs = ['Filename', 'Fancy Name', 'Takeoff', 'Duration',
                'Obs. Time', 'Airports']
        self.tableWidgetFlightBasics.setColumnCount(len(labs))
        self.tableWidgetFlightBasics.setHorizontalHeaderLabels(labs)

        for i, each in enumerate(self.listoflights):
            print("Parsing %s ..." % each, end=' ')
            bname = basename(each)
            fdict = {}
            try:
                # Parse the flight here
                cflight = fpmis.parseMIS(each)
                if cflight.hash in oldHashes:
                    self.seReview.flights.update({cflight.hash: 
                                                  oldFlights[cflight.hash]})
                else:
                    # If Auto auto review is on, do it.
                    if self.checkBoxAutoAutoReview.isChecked() is True:
                        coms = fpmis.autoReview(cflight)
                        cflight.reviewComments = coms
                    self.seReview.flights.update({cflight.hash: cflight})
                print("Success!")

                # Now fill in the table
                fdict['Filename'] = bname
                fdict['Fancy Name'] = cflight.fancyname
                fdict['Takeoff'] = str(cflight.takeoff).split(" ")[0]
                fdict['Duration'] = str(cflight.flighttime)
                fdict['Obs. Time'] = str(cflight.obstime)
                dstr = "%s to %s" % (cflight.origin, cflight.destination)
                fdict['Airports'] = dstr
                fdict['hash'] = cflight.hash
            except:
                print("Failed to parse %s" % each)
                # Fill out the table
                for key in labs:
                    if key == 'Filename':
                        fdict[key] = bname
                    else:
                        fdict[key] = ''
                fdict['hash'] = fpmis.computeHash(each)
            self.flightbasics[bname] = fdict

            # Now actually fill the table widget
            self.tableWidgetFlightBasics.insertRow(i)
            for j, hkey in enumerate(labs):
                newitem = QTableWidgetItem(str(fdict[hkey]))
                newitem.setTextAlignment(Qt.AlignCenter)
                if hkey != 'hash':
                    self.tableWidgetFlightBasics.setItem(i, j, newitem)
            self.tableWidgetFlightBasics.item(i, 0).setToolTip(each)
            self.tableWidgetFlightBasics.item(i, 1).setToolTip(fdict['hash'])

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

        # Reorder them by date if desired
        if self.checkBoxAutosortFlights.isChecked() is True:
            rord = fpmis.sortByDate(self.listoflights)
            self.listoflights = np.array(self.listoflights)[rord]
        
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

    def setFlightTableData(self):
        """
        Given a parsed flight plan, put the flight information into a nice
        table view to allow the user to easily see stuff
        """
        # Clear the table
        self.tableWidgetCurrentFlight.setRowCount(0)
        self.tableWidgetCurrentFlight.setColumnCount(0)

        # Update with the new number of colums
        self.tableWidgetCurrentFlight.setColumnCount(len(self.dataFlight.colnames[1:]))
        self.tableWidgetCurrentFlight.setHorizontalHeaderLabels(self.dataFlight.colnames[1:])

        nrowlabels = []
        for n, row in enumerate(self.dataFlight):
            self.tableWidgetCurrentFlight.insertRow(n)
            lab = "Leg %02i" % (self.dataFlight["Leg Number"][n])
            nrowlabels.append(lab)
            for m, hkey in enumerate(self.dataFlight.colnames[1:]):
                newitem = QTableWidgetItem(str(row[hkey]))
                self.tableWidgetCurrentFlight.setItem(n, m, newitem)

        self.tableWidgetCurrentFlight.setVerticalHeaderLabels(nrowlabels)

        # Resize to minimum required, then display
        self.tableWidgetCurrentFlight.resizeColumnsToContents()
        self.tableWidgetCurrentFlight.resizeRowsToContents()

        self.tableWidgetCurrentFlight.show()


def main():
    app = QApplication(sys.argv)
    form = SOFIACruiseReviewerApp()
    form.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':
    main()


import csv
import itertools

from PyQt5 import QtWidgets, QtCore
import SOFIACruiseTools.Director.FITSKeywordPanel as fkwp


class FITSKeyWordDialog(QtWidgets.QDialog, fkwp.Ui_FITSKWDialog):
    """
    Dialog box to allow for interactive selection of FITS keywords
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
        self.kwname = ''

        # Grab a few things from the parent widget to use here
        self.headers = self.parentWidget().headers
        self.fits_hdu = self.parentWidget().fits_hdu
        self.reorder_kw_widget()
        self.update_head_list()

    def reordered_head_list(self):
        """ Updates the header list if the keywords are reordered """
        self.update_head_list()
        self.txt_fitskw_status.setText('Unsaved Changes!')

    def kw_save_list(self):
        """ Saves the current keyword list as a csv """
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
                statusline = 'File Written: {0:s}'.format(self.kwname)
                self.txt_fitskw_status.setText(statusline)
            except IOError as why:
                print(str(why))
                self.txt_fitskw_status.setText('ERROR WRITING TO FILE!')

    def kw_load_list(self):
        """ Loads a list of keywords from a previously saved file """
        self.select_kw_file(kind='load')
        if self.kwname != '':
            try:
                f = open(self.kwname, 'r')
                self.headers = []
                reader = csv.reader(f)
                for row in reader:
                    self.headers.append(row)
                status_line = 'File Loaded: {0:s}'.format(self.kwname)
                self.txt_fitskw_status.setText(status_line)
            except IOError as why:
                print(str(why))
                self.txt_fitskw_status.setText('ERROR READING THE FILE!')
            finally:
                f.close()
                # Loading could have left us with a list of lists, so flatten
                self.headers = list(itertools.chain(*self.headers))
                self.reorder_kw_widget()

    def reorder_kw_widget(self):
        """ Reorders the keywords in the widget """
        self.fitskw_listing.clear()
        for key in self.headers:
            self.fitskw_listing.addItem(QtWidgets.QListWidgetItem(key))

    def get_keyword_from_user(self):
        """ Adds a keyword from user to the dictionary and widget """
        text, result = QtWidgets.QInputDialog.getText(self, 'Add Keyword',
                                                      'New Keyword:',
                                                      QtWidgets.QLineEdit.Normal,
                                                      QtCore.QDir.home().dirName())
        text = str(text)
        if result and text != '':
            text = text.strip()
            text = text.upper()
            self.fitskw_listing.addItem(QtWidgets.QListWidgetItem(text))
            self.headers.append(text)
            self.reorder_kw_widget()
            self.update_head_list()
            self.txt_fitskw_status.setText('Unsaved Changes!')

    def remove_keyword_from_list(self):
        """ Removes a selected keyword from the dictionary and widget """
        for item in self.fitskw_listing.selectedItems():
            self.fitskw_listing.takeItem(self.fitskw_listing.row(item))
        self.txt_fitskw_status.setText('Unsaved Changes!')
        self.update_head_list()
        self.reorder_kw_widget()

    def select_kw_file(self, kind='save'):
        """
        Handles saving/loading of keyword files.

        Spawn the file chooser dialog box and return the result, attempting
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
        """ Updates the dictionary with the widget """
        self.headers = []
        for j in range(self.fitskw_listing.count()):
            ched = self.fitskw_listing.item(j).text()
            self.headers.append(str(ched))
        self.headers = [hlab.upper() for hlab in self.headers]

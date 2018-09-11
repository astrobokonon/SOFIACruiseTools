
import os
import csv
import logging
from collections import OrderedDict
from pandas import read_csv
try:
    import astropy.io.fits as pyf
except ImportError:
    import pyfits as pyf


class FITSHeader(object):
    """
    Oversees the data structure that holds FITS headers
    """

    def __init__(self):

        self.logger = logging.getLogger('default')
        self.logger.debug('Starting up FITS data structure')
        self.header_vals = OrderedDict()
        self.blank_count = 0

    def add_image(self, infile, hkeys, warning_file='', rules=None, hdu=0):
        """Adds FITS header to data structure.

        Opens the FITS file given by infile and selects out the
        headers contained in headers. Adds these values to
        header_vals.

        Parameters
        ----------
        infile : str
            Name of FITS file to add.
        hkeys : list
            Header keywords to pull from ``infile``.
        warning_file : str, optional
            If any part of the header for ``infile`` fail to pass header_checker,
            then writing the details of the failure to ``warning_file``. Defaults
            to empty string if headers are not being checked.
        rules : file_checker, optional
            Rules to use to check the header, Defaults to None if headers are not
            being checked.
        hdu : int, optional
            Header Data Unit of ``infile`` to use, Defaults to 0.
        """
        header = OrderedDict()
        self.logger.info('Adding header of {}'.format(infile))
        try:
            # Read in header from FITS
            head = pyf.getheader(infile, ext=hdu)
            self.logger.debug('Successfully pulled header')
        except IOError:
            # Could not read file, return empty dictionary
            for key in hkeys:
                header[key] = ''
            self.logger.exception('Failed to open {}'.format(infile))
        else:
            # Select out the keywords of interest
            for key in hkeys:
                header[key] = head[key] if key in head else ''

        # Check the header
        if rules:
            self.logger.info('Checking header values')
            rules.warnings = {}
            rules.check(infile)
            with open(warning_file, 'a') as f:
                if rules.warnings:
                    self.logger.info('{} failed header_checker'.format(infile))
                    f.write('\nFile: {0:s}\n'.format(infile))
                    header['HEADER_CHECK'] = 'Failed'
                    # Write to file
                    for key, message in rules.warnings.items():
                        f.write('{0:s}: {1:s}\n'.format(key, message))
                else:
                    self.logger.info('{} passed header_checker'.format(infile))
                    header['HEADER_CHECK'] = 'Passed'

        # Add to data structure with the filename as key
        self.header_vals[os.path.basename(infile)] = header

    def add_images_from_log(self, logfile, hkeys):
        """Read in log from disk.

        Parameters
        ----------
        logfile : str
            Name of existing log file to read in
        hkeys : list
            List of header keys to pull from data log
        """
        self.logger.info('Reading in existing data log {}'.format(logfile))
        try:
            data_log = read_csv(logfile)
        except IOError:
            self.logger.warning('Failed to read existing data log {}'.format(
                logfile))
            return
        data_log.fillna('', inplace=True)
        data_log = data_log.to_dict('records')
        for dl in data_log:
            header = OrderedDict()
            for key in hkeys:
                if key in dl:
                    header[key] = dl[key]
                else:
                    header[key] = ''
            self.header_vals[dl['FILENAME']] = header

    def fill_data_blank_cells(self, infile, hkeys, hdu=0):
        """Fill any blank cell in table.

        If a header keyword is added after data collection has begun
        then the cells for that keyword for existing data will be
        empty. This method searches for blanks in header_vals
        for the FITS image infile. If any blanks are found, it will
        attempt to fill them from the file's header. No changes are
        made to the QtTableWidget.

        Parameters
        ----------
        infile : str
            Name of FITS file to fill header data from.
        hkeys : list
            List of FITS header keywords
        hdu : int, optional
            Header Data Unit to use when opening ``infile```. Defaults to 0.
        """
        # Read in file
        self.logger.info('Filling blank spots in data log for {}'.format(infile))
        try:
            header = pyf.getheader(infile, ext=hdu)
        except IOError:
            # Can't open the file
            # Should never happen since the file was previously opened
            self.logger.exception('Cannot open {}'.format(infile))
            return
        row = self.header_vals[os.path.basename(infile)]
        for key in hkeys:
            try:
                val = row[key]
            except KeyError:
                # Key not in this row, fill from header
                try:
                    row[key] = header[key]
                except KeyError:
                    # Key not in header either, fill with empty string
                    row[key] = ''
            else:
                # Key in this row, check if empty
                if not val:
                    # Cell is empty, try to fill from header
                    try:
                        row[key] = header[key]
                    except KeyError:
                        # Key not in header, fill with empty string
                        row[key] = ''

    def add_blank_row(self, hkeys):
        """Add blank row to the data log.

        Parameters
        ----------
        hkeys : list
            List of FITS keywords.
        """
        self.logger.debug('Adding blank row to data log.')
        blank_header = OrderedDict({key: '' for key in hkeys})
        self.blank_count += 1
        key = 'blank_{0:d}'.format(self.blank_count)
        self.header_vals[key] = blank_header

    def remove_image(self, infile):
        """Remove an observation form the data set.

        Parameters
        ----------
        infile : str
            Name of file to remove from data set.
        """
        self.logger.info('Removing {} from data log'.format(infile))
        try:
            del self.header_vals[infile]
        except KeyError:
            self.logger.exception('Unable to remove {0:s} from header_vals'.format(
                infile))

    def write_to_file(self, outname, hkeys, table=None, filenames=None):
        """Writes data structure to disk.

        Parameters
        ----------
        outname : str
            Name of file on disk to write to.
        hkeys : list
            List of FITS header keys to include in log.
        table : QTableWidget
            Name of table in GUI.
        filenames  : list
            List of filenames already included in the table.
        """
        self.logger.info('Writing data log to file')
        # Check if any field has been changed
        if table:
            self.check_user_updates(table, filenames, hkeys)

        if outname:
            fields = ['FILENAME'] + hkeys
            with open(outname, 'w') as f:
                writer = csv.DictWriter(f, fields)
                writer.writeheader()
                # Loop over filenames
                for k in self.header_vals:
                    row = {field: self.header_vals[k].get(field)
                           for field in fields}
                    row['FILENAME'] = k
                    writer.writerow(row)

    def check_user_updates(self, table, filenames, hkeys):
        """Check if the user has made any updates to the table.

        Parameters
        ----------
        table : QTableWidget
            Name of table in GUI.
        filenames : list
            List of filenames already included in the table
        """

        # Cycle through the table
        # Compare table contents with the contents of header_vals
        # Update the header_vals to the contents of table
        self.logger.debug('Looking for user updates to table')
        row_count = table.rowCount()
        col_count = table.columnCount()
        for i in range(row_count):
            fname = filenames[i]
            for j in range(col_count):
                hkey = hkeys[j]
                table_val = table.item(i, j).text()
                data_val = self.header_vals[fname][hkey]
                if table_val != data_val:
                    self.header_vals[fname][hkey] = table_val


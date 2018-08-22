
import os
import csv
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

        self.header_vals = OrderedDict()
        self.blank_count = 0

    def add_image(self, infile, hkeys, warning_file, rules=None, hdu=0):
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

        # Check the header
        if rules:
            rules.warnings = {}
            rules.check(infile)
            with open(warning_file, 'a') as f:
                if rules.warnings:
                    f.write('\nFile: {0:s}\n'.format(infile))
                    header['HEADER_CHECK'] = 'Failed'
                    # Write to file
                    for key, message in rules.warnings.items():
                        f.write('{0:s}: {1:s}\n'.format(key, message))
                else:
                    header['HEADER_CHECK'] = 'Passed'

        # Add to data structure with the filename as key
        self.header_vals[os.path.basename(infile)] = header

    def add_images_from_log(self, logfile, hkeys):
        """
        Reads in log from disk
        """
        print('logfile = ',logfile)
        data_log = read_csv(logfile)
        data_log.fillna('',inplace=True)
        data_log = data_log.to_dict('records')
        print(type(data_log))
        for dl in data_log:
            header = OrderedDict()
            for key in hkeys:
                header[key] = dl[key]
            self.header_vals[dl['FILENAME']] = header

    def fill_data_blank_cells(self, infile, hkeys, hdu=0):
        """
        Fills any blank cell in table

        If a header keyword is added after data collection has begun
        then the cells for that keyword for existing data will be
        empty. This method searches for blanks in header_vals
        for the FITS image infile. If any blanks are found, it will
        attempt to fill them from the file's header. No changes are
        made to the QtTableWidget.
        """
        # Read in file
        try:
            header = pyf.getheader(infile, ext=hdu)
        except IOError:
            # Can't open the file
            # Should never happen since the file was previously opened
            # Print to screen, but don't kill the program
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
        """
        Adds blank row to the data log
        """
        blank_header = OrderedDict({key: '' for key in hkeys})
        self.blank_count += 1
        key = 'blank_{0:d}'.format(self.blank_count)
        self.header_vals[key] = blank_header

    def remove_image(self, infile):
        """
        Removes an observation form the data set
        """
        try:
            del self.header_vals[infile]
        except KeyError:
            print('Unable to remove {0:s} from header_vals'.format(infile))

    def write_to_file(self, outname, hkeys, table=None, filenames=None):
        """
        Writes data structure to outname
        """
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
        """
        Checks if the user has made any updates to the table.
        """

        # Cycle through the table
        # Compare table contents with the contents of header_vals
        # Update the header_vals to the contents of table
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


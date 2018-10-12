"""Custom keyword values for the QA log report."""

import os
import re
import json

try:
    import astropy.io.fits as pf
except ImportError:
    import pyfits as pf

import sofia_rules
from.pyqa_utils import CaptureOutput


class QALogRules(sofia_rules.SOFIARules):

    """Class to define QA log header values and checks."""

    def __init__(self):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict={})

        self.name = 'QALog'

        keyfile = self.app_path+'keyword_dicts/qa_log/qalog_keys.json'
        with open(keyfile) as kfile:
            try:
                jkdict = json.load(kfile)
                keys = jkdict['display']
            except (ValueError, KeyError):
                raise IOError('Invalid JSON code in '+keyfile)
        if 'exclude' in jkdict:
            self.exclude_keys = jkdict['exclude']
        else:
            self.exclude_keys = []
        if 'update' in jkdict:
            self.update_keys = jkdict['update']
        else:
            self.update_keys = []

        keys = [key.strip().upper() for key in keys]
        self.preferred_keys = set(keys)
        self.key_order = keys

        # No actual QA log rules
        self.keyword_dict = {}

    def check_header(self, header):
        """Skips header validation."""
        pass

    def check(self, fname, skip_checks=False, verbose=False):
        """Reads header values from the file."""
        if not os.path.exists(fname):
            raise IOError('Input file '+fname+' does not exist')

        fname = os.path.abspath(fname)
        self.basename = os.path.basename(fname)
        if not self.basename.endswith('.fits'):
            raise TypeError('Input file '+fname+' is not FITS')

        try:
            with CaptureOutput() as output:
                hdul = pf.open(fname, ignore_missing_end=True)
                hdul.verify('silentfix')
        except Exception:
            return

        # Read key values from header
        all_keys = set(list(self.preferred_keys)+hdul[0].header.keys())
        for key in all_keys:
            if key in self.ignore_keys:
                continue
            val = self.read_value(hdul[0].header, key)
            self.key_values[key] = val

        # Store the groupname from the directory structure
        dirname = os.path.dirname(fname)
        groupname = re.sub(r'^.*/(g\d+)/?.*', r'\g<1>', dirname)
        self.key_values['GROUPNAM'] = groupname

        # Special handling for spectel, etc.
        instr = str(self.read_value(hdul[0].header,
                                    'INSTRUME')).upper().strip()
        if instr == 'EXES':
            self.key_values['WAVECENT'] = []
            wavecent = float(self.read_value(hdul[0].header, 'WAVENO0'))
        else:
            wavecent = self.read_value(hdul[0].header, 'WAVECENT')
        if instr == 'FIFI-LS':
            spectel = str(self.read_value(hdul[0].header,
                                          'DETCHAN')).strip().upper()
            if spectel == 'BLUE':
                order = str(self.read_value(hdul[0].header,
                                            'G_ORD_B')).strip().upper()
                spectel += '_ORDER_' + order
        elif instr == 'HAWC_PLUS':
            spectel1 = str(self.read_value(hdul[0].header, 'SPECTEL1'))
            spectel2 = str(self.read_value(hdul[0].header, 'SPECTEL1'))
            instcfg = str(self.read_value(
                hdul[0].header, 'INSTCFG')).upper().strip()
            if instcfg == 'POLARIZATION':
                spectel = spectel1+'&'+spectel2
            else:
                spectel = spectel1
        else:
            detchan = self.read_value(hdul[0].header, 'DETCHAN')
            spectel1 = self.read_value(hdul[0].header, 'SPECTEL1')
            spectel2 = self.read_value(hdul[0].header, 'SPECTEL2')
            dichroic = self.read_value(hdul[0].header, 'DICHROIC')
            if detchan is not None:
                # FORCAST handling
                detchan = str(detchan).upper().strip()
                if detchan == '1' or detchan == 'LW' or detchan == 'RED':
                    spectel = spectel2
                else:
                    spectel = spectel1
            else:
                if str(spectel1).upper() in ['OPEN', 'BLANK',
                                             'BLANK/DARK', 'NONE']:
                    spectel1 = None
                if str(spectel2).upper() in ['OPEN', 'BLANK',
                                             'BLANK/DARK', 'NONE',
                                             'FLT_SS10', 'FLT_SS20']:
                    spectel2 = None
                if spectel1 is None and spectel2 is None:
                    spectel = 'NONE'
                elif spectel1 is None and spectel2 is not None:
                    spectel = spectel2
                elif spectel1 is not None and spectel2 is None:
                    spectel = spectel1
                else:
                    spectel = spectel1+'&'+spectel2
            if str(dichroic).upper().strip() != 'DICHROIC':
                dichroic = 'NONE'
            else:
                dichroic = 'DUAL'
            self.key_values['DICHROIC'] = dichroic

        self.key_values['SPECTEL'] = spectel

        # And for altitude and zenith angle:
        # keep all start/end to average later
        alti_sta = self.read_value(hdul[0].header, 'ALTI_STA')
        alti_end = self.read_value(hdul[0].header, 'ALTI_END')
        alti = []
        if alti_sta is not None and alti_sta != -9999:
            alti.append(alti_sta)
        if alti_end is not None and alti_end != -9999:
            alti.append(alti_end)
        if len(alti) != 0:
            if 'ALTITUDE' in self.key_values:
                if type(self.key_values['ALTITUDE']) is not list:
                    if self.key_values['ALTITUDE'] is None:
                        self.key_values['ALTITUDE'] = []
                    else:
                        self.key_values['ALTITUDE'] = \
                            [self.key_values['ALTITUDE']]
            else:
                self.key_values['ALTITUDE'] = []
            self.key_values['ALTITUDE'] += alti

        za_start = self.read_value(hdul[0].header, 'ZA_START')
        za_end = self.read_value(hdul[0].header, 'ZA_END')
        za = []
        if za_start is not None and za_start != -9999:
            za.append(za_start)
        if za_end is not None and za_end != -9999:
            za.append(za_end)
        if len(za) != 0:
            if 'ZA' in self.key_values:
                if type(self.key_values['ZA']) is not list:
                    if self.key_values['ZA'] is None:
                        self.key_values['ZA'] = []
                    else:
                        self.key_values['ZA'] = [self.key_values['ZA']]
            else:
                self.key_values['ZA'] = []
            self.key_values['ZA'] += za

        wvc = []
        if wavecent is not None and wavecent > 0:
            wvc.append(wavecent)
        if len(wvc) != 0:
            if 'WAVECENT' in self.key_values:
                if type(self.key_values['WAVECENT']) is not list:
                    if self.key_values['WAVECENT'] is None:
                        self.key_values['WAVECENT'] = []
                    else:
                        self.key_values['WAVECENT'] = [
                            self.key_values['WAVECENT']]
            else:
                self.key_values['WAVECENT'] = []
            self.key_values['WAVECENT'] += wvc
        else:
            self.key_values['WAVECENT'] = []

        # And for raw filename: keep all filenums to format later
        filename = self.read_value(hdul[0].header, 'FILENAME')
        prodtype = self.read_value(hdul[0].header, 'PRODTYPE')
        detchan = self.read_value(hdul[0].header, 'DETCHAN')
        detchan = str(detchan).upper().strip()
        if (prodtype is None or prodtype == 'UNKNOWN') and \
                (filename is not None and filename != 'UNKNOWN'):
            if instr == 'FIFI-LS':
                mtch = re.search(r'^([0-9]{5}).*\.fits$', filename)
            elif instr == 'HAWC_PLUS':
                mtch = re.search(r'^.*HA_F\d{3,4}_([0-9]+)_.*\.fits$', filename)
                if mtch is None:
                    mtch = re.search(r'^.*_([0-9]+)\.fits$', filename)
            else:
                mtch = re.search(r'^.*([0-9]{4})(\.a)?\.fits$', filename)
            if mtch is None:
                filenum = 'UNKNOWN'
            else:
                filenum = str(int(mtch.group(1)))
            if instr == 'FORCAST' or instr == 'FIFI-LS':
                if detchan == '1' or detchan == 'LW' or detchan == 'RED':
                    filenum = 'r'+filenum
                else:
                    filenum = 'b'+filenum
            self.key_values['FILENUM'] = [filenum]
            self.key_values['TOTAL_FILES'] = [1]
        else:
            self.key_values['FILENUM'] = []
            self.key_values['TOTAL_FILES'] = [0]

        # Set some keys for non-FORCAST instruments
        if instr == 'FIFI-LS':
            self.key_values['SLIT'] = 'IFS'
            skymode = self.read_value(hdul[0].header, 'NODSTYLE')
            if skymode is not None:
                self.key_values['SKYMODE'] = skymode
            boresite = self.read_value(hdul[0].header, 'PRIMARAY')
            if boresite is not None:
                self.key_values['BORESITE'] = boresite
        elif instr == 'EXES':
            self.key_values['DICHROIC'] = 'NONE'
            skymode = self.read_value(hdul[0].header, 'INSTMODE')
            if skymode is not None:
                self.key_values['SKYMODE'] = skymode
            boresite = self.read_value(hdul[0].header, 'DATATYPE')
            if boresite is not None:
                self.key_values['BORESITE'] = boresite
            self.key_values['FILEGPID'] = 'NONE'
        elif instr == 'FLITECAM':
            skymode = self.read_value(hdul[0].header, 'INSTMODE')
            if skymode is not None:
                self.key_values['SKYMODE'] = skymode
            boresite = self.read_value(hdul[0].header, 'INSTCFG')
            if boresite is not None:
                self.key_values['BORESITE'] = boresite
        elif instr == 'HAWC_PLUS':
            skymode = self.read_value(hdul[0].header, 'INSTMODE')
            if skymode is not None:
                self.key_values['SKYMODE'] = skymode
            self.key_values['BORESITE'] = 'Nominal'
            self.key_values['SLIT'] = 'None'
            self.key_values['DICHROIC'] = 'None'
        elif instr == 'FORCAST':
            # fix the C2NC2 skymode to be less confusing
            if str(self.key_values['SKYMODE']).strip().upper() == 'C2NC4':
                self.key_values['SKYMODE'] = 'C2NC2'

        # Take exptime from calibrated files only
        if instr == 'FORCAST':
            exptime = self.read_value(hdul[0].header, 'TOTINT')
        else:
            exptime = self.read_value(hdul[0].header, 'EXPTIME')
        if instr == 'EXES':
            ptypes = ['COMBSPEC']
        else:
            ptypes = ['CALIBRATED', 'CALSPEC',
                      'WXY_RESAMPLED', 'CALIBRATE', 'CRUSH']
        if (str(prodtype).upper() in ptypes and
            exptime is not None):
            self.key_values['TOTAL_EXPTIME'] = [exptime]
        else:
            self.key_values['TOTAL_EXPTIME'] = [0]

        # Take wavshift from calspec only
        ptypes = ['CALSPEC']
        wavshift = self.read_value(hdul[0].header, 'WAVSHIFT')
        if (str(prodtype).upper() in ptypes and
            wavshift is not None):
            self.key_values['MAX_WAVSHIFT'] = [float(wavshift)]
        else:
            self.key_values['MAX_WAVSHIFT'] = []

        # Set the pipeline mode to auto to start
        self.key_values['PIPEMODE'] = 'AUTO'

        # And cal qual to nominal
        self.key_values['CALQUAL'] = 'NOMINAL'

        # Set GI COMMENTS to a space
        # This avoids an annoying Excel thing with conditional formatting,
        # applied to the CALQUAL column to the left of the GI COMMENTS
        # column.  Without the space, if you edit the CALQUAL then
        # add a comment, it automatically applies the CALQUAL formatting
        # to the GI COMMENTS.
        self.key_values['GI COMMENTS'] = ' '
        
        # Set action to append
        if self.key_values['AOR_ID'][0:2] == '90':
            self.key_values['ACTION'] = 'Append'
        else:
            self.key_values['ACTION'] = 'Update'

        # Update DATAQUAL for test slit images
        if self.key_values['INSTCFG'].split('_')[0] == 'IMAGING' and \
            self.key_values['SLIT'].split('_')[0] == 'FOR':
            self.key_values['DATAQUAL'] = 'TEST'
            self.key_values['GI COMMENTS'] = 'Acquisition Image'
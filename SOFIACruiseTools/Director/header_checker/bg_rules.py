"""Custom keyword values for the BG report."""

import os
import re
import json

import numpy as np
try:
    import astropy.io.fits as pf
except ImportError:
    import pyfits as pf

import sofia_rules
from.pyqa_utils import CaptureOutput


class BGRules(sofia_rules.SOFIARules):

    """Class to define BG header values and checks."""

    def __init__(self):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict={})

        self.name = 'BG'

        keyfile = self.app_path+'keyword_dicts/bg/bg_keys.json'
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

        # No actual BG rules
        self.keyword_dict = {}

    def check_header(self, header):
        """Skips header validation."""
        pass

    def check(self, fname, skip_checks=False, verbose=False):
        """Reads header values from the file."""
        if not os.path.exists(fname):
            raise IOError('Input file '+fname+' does not exist')

        self.basename = os.path.basename(fname)
        if not self.basename.endswith('.fits'):
            raise TypeError('Input file '+fname+' is not FITS')

        try:
            with CaptureOutput() as output:
                hdul = pf.open(fname, ignore_missing_end=True)
                hdul.verify('silentfix')
        except Exception:
            self.set_warning('FILENAME', 'FITS file is unreadable')
            return
        
        # Read key values from header
        header = hdul[0].header

        all_keys = set(list(self.preferred_keys)+header.keys())
        for key in all_keys:
            if key in self.ignore_keys:
                continue
            val = self.read_value(header, key)
            self.key_values[key] = val

        # Special handling for SPECTEL and DICHROIC
        instrume = str(self.read_value(header, 'INSTRUME')).strip().upper()
        detchan = self.read_value(header, 'DETCHAN')
        spectel1 = self.read_value(header, 'SPECTEL1')
        spectel2 = self.read_value(header, 'SPECTEL2')
        dichroic = str(self.read_value(header, 'DICHROIC')).strip().upper()
        if instrume == 'FORCAST':
            if dichroic == 'DICHROIC':
                self.key_values['DICHROIC'] = 'DUAL'
            else:
                self.key_values['DICHROIC'] = 'SINGLE'

            detchan = str(detchan).upper().strip()
            if detchan == '1' or detchan == 'LW':
                spectel = spectel2
            else:
                spectel = spectel1
        else:
            if str(spectel1).upper() in ['OPEN', 'BLANK',
                                         'BLANK/DARK', 'NONE']:
                spectel1 = None
            if str(spectel2).upper() in ['OPEN', 'BLANK',
                                         'BLANK/DARK', 'NONE']:
                spectel2 = None
            if spectel1 is None and spectel2 is None:
                spectel = 'NONE'
            elif spectel1 is None and spectel2 is not None:
                spectel = spectel2
            elif spectel1 is not None and spectel2 is None:
                spectel = spectel1
            else:
                spectel = spectel1+'&'+spectel2
        self.key_values['SPECTEL'] = spectel

        # And for altitude and zenith angle:
        # keep all start/end to average later
        alti_sta = self.read_value(header, 'ALTI_STA')
        alti_end = self.read_value(header, 'ALTI_END')
        alti = []
        if alti_sta is not None and alti_sta != -9999:
            alti.append(alti_sta)
        if alti_end is not None and alti_end != -9999:
            alti.append(alti_end)
        if len(alti) != 0:
            self.key_values['ALTITUDE'] = np.mean(alti)

        za_start = self.read_value(header, 'ZA_START')
        za_end = self.read_value(header, 'ZA_END')
        za = []
        if za_start is not None and za_start != -9999:
            za.append(za_start)
        if za_end is not None and za_end != -9999:
            za.append(za_end)
        if len(za) != 0:
            self.key_values['ZA'] = np.mean(za)

        # Special treatment for the NLINSLEV keyword, to split
        # a string array into 4 floats
        nlinslev = self.read_value(header, 'NLINSLEV')
        bglev = []
        if nlinslev is not None:
            bglev = nlinslev.split(',')
            try:
                bglev = [float(bgl.strip('[]')) for bgl in bglev]
            except ValueError:
                bglev = []
            for i in range(len(bglev)):
                self.key_values['BGLEVEL' + str(i + 1)] = bglev[i]
        else:
            bglevl_a = self.read_value(header, 'BGLEVL_A')
            bglevl_b = self.read_value(header, 'BGLEVL_B')
            if bglevl_a is not None and bglevl_a != 0 and bglevl_a != -9999:
                bglev.append(bglevl_a)
                self.key_values['BGLEVEL1'] = bglevl_a
            if bglevl_b is not None and bglevl_b != 0 and bglevl_b != -9999:
                bglev.append(bglevl_b)
                self.key_values['BGLEVEL2'] = bglevl_b
                
        # Do some statistics on the reported BG levels
        frmrate = self.read_value(header, 'FRMRATE')
        eperadu = self.read_value(header, 'EPERADU')
        if len(bglev) > 0:
            try:
                bgavg = np.mean(bglev)
                bgstd = np.std(bglev)
                self.key_values['BGAVG'] = bgavg
                self.key_values['BGSTDDEV'] = bgstd
            except ValueError:
                pass
            try:
                bglgsm = np.max(bglev) - np.min(bglev)
                self.key_values['BGLGSM'] = bglgsm
                self.key_values['BGPERCEN'] = 100 * bglgsm / np.min(bglev)
            except ValueError:
                pass
            if frmrate is not None and eperadu is not None:
                try:
                    factor = float(frmrate)*float(eperadu)/1e6
                    self.key_values['BGMES'] = bgavg * factor
                    self.key_values['BGSTDMES'] = bgstd * factor
                except ValueError:
                    pass

            

"""Custom keyword values for the fluxcal report."""

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


class FluxCalRules(sofia_rules.SOFIARules):

    """Class to define fluxcal header values and checks."""

    def __init__(self):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict={})

        self.name = 'FluxCal'

        keyfile = self.app_path+'keyword_dicts/fluxcal/fluxcal_keys.json'
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

        # No actual fluxcal rules
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
        detchan = self.read_value(header, 'DETCHAN')
        spectel1 = self.read_value(header, 'SPECTEL1')
        spectel2 = self.read_value(header, 'SPECTEL2')
        dichroic = str(self.read_value(header, 'DICHROIC')).strip().upper()
        if dichroic == 'DICHROIC' or 'BARR' in dichroic:
            self.key_values['DICHROIC'] = 'DUAL'
        else:
            self.key_values['DICHROIC'] = 'SINGLE'
        if detchan is not None:
            # FORCAST handling
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

        # Skip reading avgcalfc for now, in favor of
        # calculating it from input files in outer
        # script
        """
        # Read avg cal factors from configuration file if not
        # in header
        refcalfc = self.read_value(header, 'REFCALFC')
        refcaler = self.read_value(header, 'REFCALER')
        calfac = self.read_value(header, 'AVGCALFC')
        ecalfac = self.read_value(header, 'AVGCALER')
        instrume = self.read_value(header, 'INSTRUME')
        obstype = self.read_value(header, 'OBSTYPE')
        if (calfac is None and refcalfc is not None) and \
                instrume.upper() == 'FORCAST' and \
                obstype.upper() == 'STANDARD_FLUX':
            instcfg = self.read_value(header, 'INSTCFG')
            if instcfg.upper() == 'IMAGING_DUAL':
                dichroic = 1
            else:
                dichroic = 0
            try:
                cffile = self.app_path + \
                    'keyword_dicts/fluxcal/forcast_refcalfac.txt'
                cftable = np.loadtxt(cffile,
                                     dtype={'names': ('spectel','dichroic',
                                                      'refcalfc','refcaler'),
                                            'formats':('S8', 'i4',
                                                       'f4', 'f4')})
                idx = np.where((cftable['spectel'] == spectel.upper()) &
                               (cftable['dichroic'] == dichroic))
                if len(idx[0]) > 0:
                    calfac = cftable['refcalfc'][idx[0][0]]
                    ecalfac = cftable['refcaler'][idx[0][0]]
            except (IOError, ValueError):
                calfac = None
                ecalfac = None
        if calfac is not None:
            self.key_values['AVGCALFC'] = calfac
            self.key_values['AVGCALER'] = ecalfac

        if calfac is not None and refcalfc is not None:
            try:
                self.key_values['CALFDIFF'] = 100 * \
                	                      (calfac - refcalfc) / calfac
                self.key_values['ERCLDIFF'] = 100 * \
                	                      (ecalfac - refcaler) / ecalfac
            except (ValueError, TypeError):
                pass
        """

        # record a default value for calibration quality
        calqual = 'NOMINAL'
        calcmt = 'Assuming nominal calibration quality'

        # check for a pre-existing calqual
        hdr_calqual = str(self.read_value(header, 'CALQUAL')).upper()
        if hdr_calqual == 'BADCAL':
            calqual = hdr_calqual
            calcmt = 'CALQUAL=BADCAL in header'

        # set some warnings
        srcposx = self.read_value(header, 'SRCPOSX')
        srcposy = self.read_value(header, 'SRCPOSY')
        stcentx = self.read_value(header, 'STCENTX')
        stcenty = self.read_value(header, 'STCENTY')
        if (srcposx is not None and stcentx is not None and
                srcposy is not None and stcenty is not None):
            diffx = np.abs(srcposx - stcentx)
            diffy = np.abs(srcposy - stcenty)
            diff = np.sqrt(diffx ** 2 + diffy ** 2)
            self.key_values['SRCDIFF'] = diff

            limit = 0.3
            if diff > limit:
                calqual = 'BADCAL'
                calcmt = 'SRCDIFF > %.2f' % limit
                self.set_warning('SRCDIFF',
                                 'Difference from SRCPOS = %.2f (>%.2f)' %
                                 (diff, limit))

        # also check for bad values in photometry
        stapflx = self.read_value(header, 'STAPFLX')
        stapflxe = self.read_value(header, 'STAPFLXE')
        refcalfc = self.read_value(header, 'REFCALFC')
        refcaler = self.read_value(header, 'REFCALER')
        if stapflx is not None and (not np.isreal(stapflx) or
                                    not np.isfinite(stapflx) or
                                    stapflx == 0):
            calqual = 'BADCAL'
            calcmt = 'Bad STAPFLX'
        elif stapflxe is not None and (not np.isreal(stapflxe) or
                                     not np.isfinite(stapflxe) or
                                     stapflxe == 0):
            calqual = 'BADCAL'
            calcmt = 'Bad STAPFLXE'
        elif refcalfc is not None and (not np.isreal(refcalfc) or
                                     not np.isfinite(refcalfc) or
                                     refcalfc == 0):
            calqual = 'BADCAL'
            calcmt = 'Bad REFCALFC'
        elif refcaler is not None and (not np.isreal(refcaler) or
                                     not np.isfinite(refcaler) or
                                     refcaler == 0):
            calqual = 'BADCAL'
            calcmt = 'Bad REFCALER'

        # and for bad dataqual
        dataqual = self.read_value(header, 'DATAQUAL')
        if dataqual is not None:
            dataqual = str(dataqual).upper()
            if dataqual not in ['UNKNOWN', 'NOMINAL']:
                calqual = 'BADCAL'
                calcmt = 'Bad DATAQUAL'

        self.key_values['CALQUAL'] = calqual
        if calqual == 'BADCAL':
            self.set_warning('CALQUAL', calcmt)

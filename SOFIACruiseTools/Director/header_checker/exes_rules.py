"""Custom checks for the EXES instrument."""

from __future__ import print_function, absolute_import
import os
import json
from . import sofia_rules


class EXESRules(sofia_rules.SOFIARules):

    """Class to define EXES header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'EXES'

        keyfile = self.app_path+'keyword_dicts/EXES/EXES_keys.json'
        with open(keyfile) as kfile:
            try:
                jkdict = json.load(kfile)
                keys = jkdict['display']
            except (ValueError, KeyError):
                raise IOError('Invalid JSON code in '+keyfile)
        if 'exclude' in jkdict:
            self.exclude_keys = jkdict['exclude']
        if 'update' in jkdict:
            self.update_keys = jkdict['update']

        keys = [key.strip().upper() for key in keys]
        self.preferred_keys = set(keys)
        self.key_order = keys

        # Read EXES rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/EXES/EXES_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        exes_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(exes_dict)

    def check_header(self, header):
        """Perform any custom checks for EXES header validation."""

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # many modes can be best determined from filename
        filename = self.read_value(header, 'FILENAME')
        fnlist = filename.lower().split('.')
        if len(fnlist) == 4:
            obj, mode, fnum, ext = fnlist
        else:
            return

        # check for datatype=OTHER
        datatype = self.read_value(header, 'DATATYPE')
        if (obj == 'camera' or obj == 'thruslit'):
            if str(datatype).upper() != 'IMAGE':
                self.set_update('DATATYPE', datatype, 'IMAGE',
                                'Updating DATATYPE to match filename')
                datatype = 'IMAGE'
        elif obj != 'pupil' and str(datatype).upper() != 'SPECTRAL':
            self.set_update('DATATYPE', datatype, 'SPECTRAL',
                            'Updating DATATYPE to match filename')
            datatype = 'SPECTRAL'

        # check for obstype - must be FLAT for flats
        obstype = self.read_value(header, 'OBSTYPE')
        if mode == 'flat' and str(obstype).upper() != 'FLAT':
            self.set_update('OBSTYPE', obstype, 'FLAT',
                            'Updating OBSTYPE to match filename')

        # check for missing END values
        alti_end = self.read_value(header, 'ALTI_END')
        alti_sta = self.read_value(header, 'ALTI_STA')
        za_end = self.read_value(header, 'ZA_END')
        za_start = self.read_value(header, 'ZA_START')
        try:
            alti_sta = float(alti_sta)
            if int(alti_sta) == -9999:
                alti_sta = None
        except (ValueError, TypeError):
            alti_sta = None
        if alti_sta is not None and (alti_end is None or
                                     int(alti_end) == -9999):
            self.set_update('ALTI_END', alti_end, alti_sta,
                            'Replacing missing ALTI_END with ALTI_STA')
        try:
            za_start = float(za_start)
            if int(za_start) == -9999:
                za_start = None
        except (ValueError, TypeError):
            za_start = None
        if za_start is not None and (za_end is None or
                                     int(za_end) == -9999):
            self.set_update('ZA_END', za_end, za_start,
                            'Replacing missing ZA_END with ZA_START')

        # check for wrong instcfg
        instcfg = self.read_value(header, 'INSTCFG')
        spectel1 = self.read_value(header, 'SPECTEL1')
        if (str(spectel1).upper() == 'NONE' and
                datatype.upper() == 'SPECTRAL'):
            if str(instcfg).upper() == 'HIGH_MED':
                self.set_update('INSTCFG', instcfg, 'MEDIUM',
                                'Updating INSTCFG from SPECTEL1')
            elif str(instcfg).upper() == 'HIGH_LOW':
                self.set_update('INSTCFG', instcfg, 'LOW',
                                'Updating INSTCFG from SPECTEL1')

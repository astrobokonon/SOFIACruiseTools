"""Custom checks for the HAWC instrument."""

from __future__ import print_function, absolute_import 
import os
import json
import re
from . import sofia_rules


class HAWCRules(sofia_rules.SOFIARules):

    """Class to define HAWC header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'HAWC'

        keyfile = self.app_path+'keyword_dicts/HAWC/HAWC_keys.json'
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

        # Read HAWC rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/HAWC/HAWC_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        hawc_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(hawc_dict)

    def check_header(self, header):

        # First: fix a crucial keyword -- the requirements
        # checked in the generic rules depend on it.
        scanpatt = self.read_value(header, 'SCANPATT')
        scnpatt = self.read_value(header, 'SCNPATT')
        if scanpatt is not None:
            self.set_update('SCANPATT', scanpatt, None,
                            'Removing bad SCANPATT keyword')
            if scnpatt is None:
                self.set_update('SCNPATT', scnpatt, scanpatt,
                                'Replacing SCNPATT with value from SCANPATT')
            header['SCNPATT'] = scanpatt

        # Then call the generic sofia rules
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # Check for bad obsid key
        ob_sid = self.read_value(header, 'OB_SID')
        obs_id = self.read_value(header, 'OBS_ID')
        if ob_sid is not None:
            self.set_update('OB_SID', ob_sid, None,
                            'Removing bad OBS_ID keyword')
            if obs_id is None:
                self.set_update('OBS_ID', obs_id, ob_sid,
                                'Replacing OBS_ID with value from OB_SID')

        # Check for bad missn key
        bad = self.read_value(header, 'MISSN_ID')
        good = self.read_value(header, 'MISSN-ID')
        if bad is not None:
            self.set_update('MISSN_ID', bad, None,
                            'Removing bad MISSN_ID keyword')
            if good is None:
                self.set_update('MISSN-ID', good, bad,
                                'Replacing MISSN-ID with value from MISSN_ID')

        # Exclude non-science diagnostic modes
        # For FS12 only
        diagmode = self.read_value(header, 'DIAGMODE')
        if not (diagmode is None or
                str(diagmode).upper().strip() == 'UNKNOWN' or
                str(diagmode).strip() == ''):
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Excluding diagnostic file (%s)' % diagmode)


        # Standardize blank CALMODE so it can be grouped on
        strcalmode = str(self.read_value(header, 'CALMODE')).upper().strip()
        if (strcalmode == ''):
            self.set_update('CALMODE', calmode, 'UNKNOWN',
                            'Standardizing blank calmode')

        # Modify filegpid and scriptid usage
        # OC4L: scriptid didn't exist, filegpid contained what is now scriptid
        # OC5E: filegpid and scriptid both exist, set to same number
        filegpid = self.read_value(header, 'FILEGPID')
        scriptid = self.read_value(header, 'SCRIPTID')
        if scriptid is None:
            # set scriptid from filegpid if is a string of numbers (OC5E)
            if filegpid is not None and re.match('^\d+$', str(filegpid)):
                self.set_update('SCRIPTID', scriptid, str(filegpid),
                                'Setting SCRIPTID from FILEGPID')
                scriptid = filegpid

        # Set filegpid to object + instcfg + spectels if it is 
        # just a string of numbers (OC4L and OC5E)
        if (filegpid is None or
                re.match('^\d+$', str(filegpid)) or
                str(filegpid).strip().upper() == 'UNKNOWN'):
            objname = str(self.read_value(header, 'OBJECT')).strip().upper()
            objname = re.sub('\s+', '_', objname)
            
            spectel1 = str(self.read_value(header, 'SPECTEL1'))
            spec1 = spectel1.strip().upper().replace('_', '')
            spectel2 = str(self.read_value(header, 'SPECTEL2'))
            spec2 = spectel2.strip().upper().replace('HAW_','').replace('_','')

            instcfg = str(self.read_value(header, 'INSTCFG')).strip().upper()
            if instcfg == 'TOTAL_INTENSITY':
                cfg = 'IMA'
            elif instcfg == 'POLARIZATION':
                cfg = 'POL'
            else:
                cfg = 'UNK'

            new_filegp = '%s_%s_%s_%s' % (objname, cfg, spec1, spec2)
            self.set_update('FILEGPID', filegpid, new_filegp,
                            'Updating FILEGPID to object + instcfg + '
                            'spectel1 + spectel2')
        

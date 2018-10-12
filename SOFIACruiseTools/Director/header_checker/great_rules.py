"""Custom checks for the GREAT instrument."""

from __future__ import print_function
import os
import json
from . import sofia_rules
import numpy as np


class GREATRules(sofia_rules.SOFIARules):

    """Class to define GREAT header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'GREAT'

        keyfile = self.app_path+'keyword_dicts/GREAT/GREAT_keys.json'
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

        # Read GREAT rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/GREAT/GREAT_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        great_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(great_dict)

    def check_header(self, header):

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # fix AOR_ID, PLANID
        # if OT, planid will either be: (1) 7 chars with one underscore(xx_xxxx) or (2) at least 9 chars
        #  with two underscores (xx_xxxx_x). For case (1): leave planid alone; if aor_id is 'UNKNOWN',
        #  replace with planid_1. For case (2): if aor_id is 'UNKNOWN', copy planid to aorid, create new
        #  planid with first 7 chars of its old value
        # if GT, planid could be anything, but is typically something like: 201405_GR_02, which almost
        #  matches case (2) (but not quite). PLANID for GT should be left alone, and AOR_ID set to 'UNKNOWN'
        planid = self.read_value(header, 'PLANID')
        if planid:
            aor_id = self.read_value(header, 'AOR_ID')
            if aor_id == 'UNKNOWN' or aor_id == None:
                planid_spl = planid.split('_')
                if len(planid_spl) == 3 and len(planid_spl[0]) == 2 and len (planid_spl[1]) == 4:
                    # case (2) above
                    self.set_update('AOR_ID', aor_id, planid, 'AOR_ID copied from PLANID field')
                    self.set_update('PLANID', planid, planid[0:7], 'PLANID created from AOR_ID')
                else:
                    # case (1) above
                    if planid == 'UNKNOWN':
                        if not aor_id:
                            self.set_update('AOR_ID', aor_id, 'UNKNOWN', 'No AOR_ID, UNKNOWN PLANID: set AOR_ID to UNKNOWN')
                    else:
                        if len(planid_spl) == 2 and len(planid_spl[0]) == 2 and len (planid_spl[1]) == 4:
                            #valid planid, 
                            self.set_update('AOR_ID', aor_id, planid+'_1', 'No AOR_ID, assign using PLANID')
                        else:
                            # improperly formatted plan--probably from GT flights
                            if not aor_id:
                                self.set_update('AOR_ID', aor_id, 'UNKNOWN', 'Generate AOR_ID using PLANID')            
        else:
             self.set_update('PLANID', planid, 'UNKNOWN', 'Missing PLANID, set to UNKNOWN')
             self.set_update('AOR_ID', aor_id, 'UNKNOWN', 'Missing AOR_ID, set to UNKNOWN')   

        # fix obsra; in fits version 2.8, it is incorrect by a factor of 15
        #  (an extra factor of degrees to hours conversion)
        fits_vers = self.read_value(header, 'FITSVERS')
        obsra = self.read_value(header, 'OBSRA')

        fix_fits_vers = ['2.6', '2.8']
        if fits_vers in fix_fits_vers:
            history = self.read_value(header, 'HISTORY')
            obsra_updated = False
            if history:
                for line in history:
                    if 'OBSRA' in line:
                        obsra_updated = True
            if not obsra_updated:
                self.set_update('OBSRA', obsra, obsra*15., 'Corrected OBSRA for incorrect unit conversion.')
        cur_spectel = self.read_value(header, 'SPECTEL1')
        if cur_spectel == 'UNKNOWN':
            freq = self.read_value(header, 'RESTFREQ') / 1.0e6
            new_spectel = False
            if freq > 1.23 and freq < 1.41:
                new_spectel = 'GRE_L1A'
            elif freq > 1.42 and freq < 1.53:
                new_spectel = 'GRE_L1B'
            elif freq > 1.80 and freq < 2.10:
                new_spectel = 'GRE_L2'
            elif freq > 2.48 and freq < 2.60:
                new_spectel = 'GRE_M1'
            elif freq > 2.65 and freq < 2.71:
                new_spectel = 'GRE_M2'
            elif freq > 4.7 and freq < 4.8:
                new_spectel = 'GRE_H'
            if new_spectel:
                self.set_update('SPECTEL1', cur_spectel, new_spectel, 'SPECTEL1 assigned based on frequency (was UNKNOWN)')
        cur_instcfg = self.read_value(header, 'INSTCFG')
        if cur_instcfg != 'DUAL_CHANNEL':
            self.set_update('INSTCFG', cur_instcfg, 'DUAL_CHANNEL', 'INSTCFG assigned the default value of DUAL_CHANNEL')
        
                

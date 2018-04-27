"""Custom checks for the FPI instrument."""

from __future__ import print_function, absolute_import 
import os
import json
import re
from . import sofia_rules


class FPIRules(sofia_rules.SOFIARules):

    """Class to define FPI header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'FPI'

        keyfile = self.app_path+'keyword_dicts/FPI/FPI_keys.json'
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

        # Read FPI rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/FPI/FPI_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        fpi_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(fpi_dict)

    def check_header(self, header):
        """Perform any custom checks for FPI header validation."""

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------


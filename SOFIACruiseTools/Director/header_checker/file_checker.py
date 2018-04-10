"""Locate files, identify verification rules, run verification."""

from __future__ import print_function, absolute_import

import os

from . import sofia_rules
from . import forcast_rules
from . import flitecam_rules
from . import exes_rules
from . import hawc_rules
from . import great_rules
from . import fifi_ls_rules
from . import fpi_rules


class FileChecker(object):
    """Class to associate verification rules with FITS files."""

    def __init__(self):

        try:
            self.user = os.environ['USER']
        except KeyError:
            self.user = 'UNKNOWN'
        self.kwdicts = {}
        self.name = None
        self.instrument = None
        self.rules = None


    def choose_rules(self, instrument, dictfile=None, name=None):
        """Associate appropriate rules with a given file."""
        kwdict = None
        if instrument == 'FORCAST':
            name = 'FORCAST'
            crl = forcast_rules.FORCASTRules(dictfile=dictfile,
                                             kwdict=kwdict)
        elif instrument == 'FLITECAM':
            name = 'FLITECAM'
            crl = flitecam_rules.FLITECAMRules(dictfile=dictfile,
                                               kwdict=kwdict)
        elif instrument == 'EXES':
            name = 'EXES'
            crl = exes_rules.EXESRules(dictfile=dictfile,
                                       kwdict=kwdict)
        elif (instrument == 'HAWC' or instrument == 'HAWC+' or
              instrument == 'HAWC_PLUS'):
            name = 'HAWC'
            crl = hawc_rules.HAWCRules(dictfile=dictfile,
                                       kwdict=kwdict)
        elif instrument == 'GREAT':
            name = 'GREAT'
            crl = great_rules.GREATRules(dictfile=dictfile,
                                         kwdict=kwdict)
        elif instrument == 'FIFI-LS':
            name = 'FIFI-LS'
            crl = fifi_ls_rules.FIFILSRules(dictfile=dictfile,
                                            kwdict=kwdict)
        elif instrument == 'FPI_PLUS':
            name = 'FPI'
            crl = fpi_rules.FPIRules(dictfile=dictfile,
                                     kwdict=kwdict)
        else:
            name = 'SOFIA'
            crl = sofia_rules.SOFIARules(dictfile=dictfile,
                                         kwdict=kwdict)
        self.instrument = name

        # Check for stored keyword dictionary
        # (this avoids re-parsing the file)
        name = name.upper()
        if name in self.kwdicts:
            kwdict = self.kwdicts[name]
        else:
            kwdict = None

        self.kwdicts[name] = crl.keyword_dict
        self.rules = crl
        return crl

"""Custom checks for the FLITECAM instrument."""

from __future__ import print_function, absolute_import 
import os
import re
import json
from . import sofia_rules


class FLITECAMRules(sofia_rules.SOFIARules):

    """Class to define FLITECAM header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'FLITECAM'

        keyfile = self.app_path+'keyword_dicts/FLITECAM/FLITECAM_keys.json'
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

        # Read FLITECAM rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/FLITECAM/FLITECAM_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        fcam_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(fcam_dict)

    def check_header(self, header):
        """Perform any custom checks for FLITECAM header validation."""

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # Get some necessary values from the header
        # (will be None if not in header)
        modekeys = ['CHOPPING', 'NODDING', 'DITHER',
                    'MAPPING', 'SCANNING']
        for mkey in modekeys:
            oval = self.read_value(header, mkey)
            if oval is not None and type(oval) is not bool:
                if str(oval).strip().upper() == 'TRUE':
                    nval = True
                else:
                    nval = False
                self.set_update(mkey, oval, nval,
                                'Correcting type', dtype='log')

        # Check for invalid keywords
        filegpid = self.read_value(header, 'FILEGPID')
        if str(filegpid).lower().startswith('file group'):
            self.set_update('FILEGPID', filegpid, 'UNKNOWN',
                            'Fixing invalid keyword')
        wavecent = self.read_value(header, 'WAVECENT')
        if str(wavecent).lower().startswith('central wave'):
            self.set_update('WAVECENT', wavecent, -9999.0,
                            'Fixing invalid keyword', dtype='flt')
        aot_id = self.read_value(header, 'AOT_ID')
        if str(aot_id).lower().startswith('astronomical'):
            self.set_update('AOT_ID', aot_id, 'UNKNOWN',
                            'Fixing invalid keyword', dtype='str')
        obserno = self.read_value(header, 'OBSERNO')
        if str(obserno).lower().startswith('running count'):
            self.set_update('OBSERNO', obserno, '-9999',
                            'Fixing invalid keyword', dtype='int')
        for key in header.keys():
            if re.match(r'^((IDL)|(LINE))\d+$', key):
                val = self.read_value(header, key)
                self.set_update(key, val, None,
                                'Deleting invalid keyword')

        # Check datatype
        datatype = self.read_value(header, 'DATATYPE')
        if str(datatype).upper() == 'SPECTROSCOPY':
            self.set_update('DATATYPE', datatype, 'SPECTRAL',
                            'Correcting to standard value')
        elif (str(datatype).upper() != 'IMAGE' and
              str(datatype).upper() != 'SPECTRAL'):
            self.set_update('DATATYPE', datatype, 'IMAGE',
                            'Correcting to standard value')

        # Check for missing source type
        srctype = self.read_value(header, 'SRCTYPE')
        if srctype is None:
            self.set_update('SRCTYPE', srctype, 'UNKNOWN',
                            'Adding missing keyword',
                            comment='Source type')

        # Check for missing SLIT/SPECTEL2
        slit = self.read_value(header, 'SLIT')
        spectel2 = self.read_value(header, 'SPECTEL2')
        slitpos = self.read_value(header, 'SLITPOS')
        if slitpos == 1:
            slitval = 'FLT_SS20'
            msg = 'SLITPOS=1, assuming wide slit'
        else:
            slitval = 'NONE'
            msg = 'SLITPOS=0'
        if slit not in ['NONE', 'FLT_SS10', 'FLT_SS20']:
            self.set_update('SLIT', slit, slitval, msg,
                            comment='Instrument slit in use')
        if spectel2 not in ['NONE', 'FLT_SS10', 'FLT_SS20']:
            self.set_update('SPECTEL2', spectel2, slitval, msg)

        # Fix SPECTEL1 from FCFILTA/FCFILTB
        spectel1 = self.read_value(header, 'SPECTEL1')
        fcfilta = str(self.read_value(header, 'fcfilta')).strip().upper()
        fcfiltb = str(self.read_value(header, 'fcfiltb')).strip().upper()
        img_filter = None
        gri_filter = None
        if (fcfilta == 'OPEN' or
                fcfilta == 'NONE'):
            fcfilta = None
        if (fcfiltb == 'OPEN' or
                fcfiltb == 'NONE'):
            fcfiltb = None
        if fcfilta is None and fcfiltb is None:
            img_filter = None
        elif fcfilta is None and fcfiltb is not None and \
                not re.search('GRISM', fcfiltb):
            img_filter = fcfiltb
        elif fcfilta is not None and fcfiltb is None and \
                not re.search('GRISM', fcfilta):
            img_filter = fcfilta
        else:
            if fcfilta is not None and re.search('GRISM', fcfilta):
                gri_filter = fcfilta
                img_filter = fcfiltb
            elif fcfiltb is not None and re.search('GRISM', fcfiltb):
                gri_filter = fcfiltb
                img_filter = fcfilta
            else:
                img_filter = 'UNKNOWN'
        if img_filter is None and gri_filter is None:
            new_spec = 'NONE'
        elif gri_filter is not None:
            if img_filter is None:
                new_spec = 'UNKNOWN'
            elif re.search('GRISMA', gri_filter):
                if img_filter.startswith('K'):
                    new_spec = 'FLT_A2_KL'
                elif img_filter.startswith('H'):
                    new_spec = 'FLT_A3_Hw'
                elif img_filter.startswith('L'):
                    new_spec = 'FLT_A1_LM'
                elif re.search('BLANK', img_filter):
                    new_spec = 'FLT_DRK'
                else:
                    new_spec = 'UNKNOWN'
            elif re.search('GRISMB', gri_filter):
                if img_filter.startswith('J'):
                    new_spec = 'FLT_B3_J'
                elif img_filter.startswith('H'):
                    new_spec = 'FLT_B2_Hw'
                elif img_filter.startswith('L'):
                    new_spec = 'FLT_B1_LM'
                elif re.search('BLANK', img_filter):
                    new_spec = 'FLT_DRK'
                else:
                    new_spec = 'UNKNOWN'
            elif re.search('GRISMC', gri_filter):
                if img_filter.startswith('H'):
                    new_spec = 'FLT_C4_H'
                elif img_filter.startswith('K'):
                    new_spec = 'FLT_C3_Kw'
                elif img_filter.startswith('L'):
                    new_spec = 'FLT_C2_LM'
                elif re.search('BLANK', img_filter):
                    new_spec = 'FLT_DRK'
                else:
                    new_spec = 'UNKNOWN'
            elif re.search('BLANK', gri_filter):
                if re.search('BLANK', img_filter):
                    new_spec = 'FLT_DRK'
            else:
                new_spec = 'UNKNOWN'
        else:
            if img_filter.startswith('J'):
                new_spec = 'FLT_J'
            elif img_filter.startswith('H'):
                new_spec = 'FLT_H'
            elif img_filter.startswith('K'):
                new_spec = 'FLT_K'
            elif re.search('ICE', img_filter):
                new_spec = 'FLT_ICE_308'
            elif re.search('PAH', img_filter):
                new_spec = 'FLT_PAH_329'
            elif re.search('PA.*CONT', img_filter):
                new_spec = 'FLT_Pa_cont'
            elif re.search('PA-ALPHA', img_filter):
                new_spec = 'FLT_Pa'
            elif re.search('NBL', img_filter):
                new_spec = 'FLT_NbL'
            elif re.search('NBM', img_filter):
                new_spec = 'FLT_NbM'
            elif re.search('BLANK', img_filter):
                new_spec = 'FLT_DRK'
            else:
                new_spec = 'UNKNOWN'
        if (fcfilta == 'BLANK-DARK' or
                fcfiltb == 'BLANK-DARK'):
            new_spec = 'FLT_DRK'

        if spectel1 != new_spec:
            self.set_update('SPECTEL1', spectel1, new_spec,
                            'Correcting SPECTEL1 from FCFILTA/B')

        # Check for OBSTYPE and correct it if SPECTEL1 is FLT_DRK
        obstype = self.read_value(header, 'OBSTYPE')
        if new_spec == 'FLT_DRK':
            new_obs = 'DARK'
        else:
            new_obs = obstype

        if obstype != new_obs:
            self.set_update('OBSTYPE', obstype, new_obs,
                            'Correcting OBSTYPE from SPECTEL1')

        # Check for bad WCS keywords, remove them if present
        keys = ['PC1_1', 'PC1_2', 'PC2_1', 'PC2_2']
        for k in keys:
            val = self.read_value(header, k)
            if val is not None:
                self.set_update(k, val, None,
                                'Removing bad WCS keywords')

"""Custom checks for the FIFI-LS instrument."""

from __future__ import print_function, absolute_import 
import os
import json
import re
from . import sofia_rules

class FIFILSRules(sofia_rules.SOFIARules):

    """Class to define FIFI-LS header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'FIFI-LS'

        keyfile = self.app_path+'keyword_dicts/FIFI_LS/FIFI_LS_keys.json'
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

        # Read FIFI_LS rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/FIFI_LS/FIFI_LS_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        fifi_ls_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(fifi_ls_dict)

    def check_header(self, header):
        """Perform any custom checks for FIFI_LS header validation."""

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # check that at least one of RAMPLN_B and RAMPLN_R are
        # nonzero
        rampln_b = self.read_value(header, 'RAMPLN_B')
        rampln_r = self.read_value(header, 'RAMPLN_R')
        if rampln_b is None:
            rampln_b = 0
        if rampln_r is None:
            rampln_r = 0
        try:
            nramp = rampln_b + rampln_r
            if nramp == 0:
                self.set_warning('RAMPLN_B',
                                 'At least one of RAMPLN_B and RAMPLN_R '
                                 'must be non-zero.')
                self.set_warning('RAMPLN_R',
                                 'At least one of RAMPLN_B and RAMPLN_R '
                                 'must be non-zero.')
        except (TypeError):
            pass


        c_chopln = self.read_value(header, 'C_CHOPLN')
        c_cyc_b = self.read_value(header, 'C_CYC_B')
        g_psup_b = self.read_value(header, 'G_PSUP_B')
        g_psdn_b = self.read_value(header, 'G_PSDN_B')
        g_cyc_b = self.read_value(header, 'G_CYC_B')
        exptime = self.read_value(header, 'EXPTIME')

        try:
            real_exptime = (c_chopln * c_cyc_b * (g_psup_b+g_psdn_b) * \
                            g_cyc_b)/250.
            if abs(real_exptime - exptime) > 0.01:
                self.set_update('EXPTIME', exptime, real_exptime,
                                'Setting exposure time from chop/read '
                                'keywords')
        except (TypeError):
            real_exptime = exptime

        # correct NODSTYLE to standard value
        nodstyle = self.read_value(header, 'NODSTYLE')
        if nodstyle is not None:
            if str(nodstyle).upper().strip() == 'SYMMETRIC':
                self.set_update('NODSTYLE', nodstyle, 'NMC',
                                'Updating to standard value')
            if str(nodstyle).upper().strip() == 'ASYMMETRIC':
                self.set_update('NODSTYLE', nodstyle, 'C2NC2',
                                'Updating to standard value')

        # copy date from DATE to DATE-OBS and UTCSTART/END for
        # flights earlier than OC3-2
        date = self.read_value(header, 'DATE')
        dateobs = self.read_value(header, 'DATE-OBS')
        utcstart = self.read_value(header, 'UTCSTART')
        utcend = self.read_value(header, 'UTCEND')
        missn_id = str(self.read_value(header, 'MISSN-ID'))
        mid = re.match('.*_F(\d{3,4})$', missn_id)
        if (mid and int(mid.group(1)) <= 206) and date is not None:
            if dateobs!=date:
                self.set_update('DATE-OBS', dateobs, date,
                                'Setting DATE-OBS from DATE for flight <= 206')
            utdate, uttime = date.split('T')
            if utcstart != uttime:
                self.set_update('UTCSTART', utcstart, uttime,
                                'Setting UTCSTART from DATE for flight <= 206')

            import datetime as dt
            dtime = [int(d) for d in utdate.split('-')] + \
                    [int(t) for t in uttime.split(':')]
            try:
                dtime = dt.datetime(*dtime)
                endtime = dtime + dt.timedelta(0, real_exptime)
                endtime = endtime.strftime('%H:%M:%S')
                if utcend != endtime:
                    self.set_update('UTCEND', utcend, endtime,
                                    'Setting UTCEND from DATE+'
                                    'EXPTIME for flight <= 206')
            except ValueError:
                pass

        # modify obsids from file path/name, to eliminate
        # duplicate values and bad file numbers
        obsid = self.read_value(header, 'OBS_ID')
        fname = self.fullname
        if obsid is not None and fname != '':
            mid = re.match('^(.*_F(\d{3,4})[BR])(\d+)$', obsid)
            mpth = re.match('^.*Folder_?(\d+).*$', fname)
            fnum = re.match('^(\d+).*$', self.basename)
            update = False
            if mid:
                if fnum:
                    oldnum = fnum.group(1)
                else:
                    oldnum = mid.group(3)
                newid = mid.group(1) + oldnum
                mid = re.match('^(.*_F(\d{3,4})[BR])(\d+)$', newid)
                update = True
            if mid and mpth:
                newnum = mpth.group(1) + oldnum
                newid = mid.group(1) + newnum
            if update and obsid != newid:
                self.set_update('OBS_ID', obsid, newid,
                                'Setting file number from Folder number')

        # set obstype to flat for skydip files
        objname = self.read_value(header, 'OBJECT')
        obstype = str(self.read_value(header, 'OBSTYPE')).upper().strip()
        if objname is not None:
            if 'skydip' in objname.strip().lower() and obstype != 'FLAT':
                self.set_update('OBSTYPE', obstype, 'FLAT',
                                'Setting OBSTYPE=FLAT for skydip files')
        else:
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Excluding file with no OBJECT keyword')


        # get central wavelength
        # also set filegpid from filegp_b or filegp_r
        detchan = str(self.read_value(header, 'DETCHAN')).upper().strip()
        wavecent = self.read_value(header, 'WAVECENT')
        filegpid = self.read_value(header, 'FILEGPID')
        if detchan == 'RED':
            wave_r = self.read_value(header, 'G_WAVE_R')
            if wave_r is not None:
                if wavecent is None or wavecent != wave_r:
                    self.set_update('WAVECENT', wavecent, wave_r,
                                    'Setting wavecent from G_WAVE_R')
            filegp_r = self.read_value(header, 'FILEGP_R')
            if filegp_r is not None and filegpid is None:
                    self.set_update('FILEGPID', filegpid, filegp_r,
                                    'Setting FILEGPID from FILEGP_R')
        else:
            wave_b = self.read_value(header, 'G_WAVE_B')
            if wave_b is not None:
                if wavecent is None or wavecent != wave_b:
                    self.set_update('WAVECENT', wavecent, wave_b,
                                    'Setting wavecent from G_WAVE_B')
            filegp_b = self.read_value(header, 'FILEGP_B')
            if filegp_b is not None and filegpid is None:
                    self.set_update('FILEGPID', filegpid, filegp_b,
                                    'Setting FILEGPID from FILEGP_B')

"""Custom checks for the FORCAST instrument."""

from __future__ import print_function, absolute_import

import os
import re
import json
import numpy as np
from . import sofia_rules

class FORCASTRules(sofia_rules.SOFIARules):

    """Class to define FORCAST header validation rules."""

    def __init__(self, dictfile=None, kwdict=None):

        # Call the parent constructor
        sofia_rules.SOFIARules.__init__(self, kwdict=kwdict)

        self.name = 'FORCAST'

        keyfile = self.app_path+'keyword_dicts/FORCAST/FORCAST_keys.json'
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

        # Read FORCAST rules
        if kwdict is None:
            if dictfile is None:
                dictfile = self.app_path + \
                    'keyword_dicts/FORCAST/FORCAST_rules.json'
            if not os.path.isfile(dictfile):
                dictfile = None

        fcast_dict = self.read_keyword_dict(dictfile=dictfile, kwdict=kwdict)
        self.keyword_dict.update(fcast_dict)

    def check_header(self, header):
        """Perform any custom checks for FORCAST header validation."""

        # Call the generic sofia rules first
        sofia_rules.SOFIARules.check_header(self, header)

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # Get some necessary values from the header
        # (will be None if not in header)
        aor_id = self.read_value(header, 'AOR_ID')
        datatype = self.read_value(header, 'DATATYPE')
        detchan = self.read_value(header, 'DETCHAN')
        dichroic = self.read_value(header, 'DICHROIC')
        filt4_s = self.read_value(header, 'FILT4_S')
        iconfig = self.read_value(header, 'ICONFIG')
        instcfg = self.read_value(header, 'INSTCFG')
        instmode = self.read_value(header, 'INSTMODE')
        obstype = self.read_value(header, 'OBSTYPE')
        planid = self.read_value(header, 'PLANID')
        skymode = self.read_value(header, 'SKYMODE')
        slit = self.read_value(header, 'SLIT')
        spectel1 = self.read_value(header, 'SPECTEL1')
        spectel2 = self.read_value(header, 'SPECTEL2')

        # Fix detchan for change to string values
        sdetchan = str(detchan).upper().strip()
        if sdetchan =='0':
            self.set_update('DETCHAN', detchan, 'SW',
                            'Updating DETCHAN to string value')
        elif sdetchan =='1':
            self.set_update('DETCHAN', detchan, 'LW',
                            'Updating DETCHAN to string value')

        if sdetchan == '1' or sdetchan == 'LW':
            detchan = 1
        else:
            detchan = 0

        # Set some variable ranges
        img_instmode = ['C2', 'C2N', 'C2NC2']
        gri_instmode = ['C2', 'NXCAC', 'C2N', 'SLITSCAN']
        gri_xd_instmode = gri_instmode + ['N']

        img_slit = ['NONE', 'FOR_LS24', 'FOR_LS47', 'FOR_SS24']
        gri_ls_slit = ['FOR_LS24', 'FOR_LS47']
        gri_xd_slit = ['FOR_SS24']

        swc_dichroic = ['Mirror (swc)']
        lwc_dichroic = ['Open (lwc)']
        dual_dichroic = ['Dichroic', 'Barr #3']

        # Read allowed spectels from keyword dictionary
        sp1_range = self.keyword_dict['SPECTEL1']['drange'][0]['value']
        sp1_range = sp1_range.split(',')
        sp1_range = [s.strip() for s in sp1_range]
        sp2_range = self.keyword_dict['SPECTEL2']['drange'][0]['value']
        sp2_range = sp2_range.split(',')
        sp2_range = [s.strip() for s in sp2_range]

        # Sort spectels by mode
        img_swc_spectel = []
        img_lwc_spectel = []
        gri_swc_spectel = []
        gri_lwc_spectel = []
        gri_xd_spectel = []
        for sp1 in sp1_range:
            if sp1.upper().startswith('FOR_F'):
                img_swc_spectel.append(sp1)
            elif sp1.upper().startswith('FOR_X'):
                gri_xd_spectel.append(sp1)
            else:
                gri_swc_spectel.append(sp1)
        for sp2 in sp2_range:
            if sp2.upper().startswith('FOR_F'):
                img_lwc_spectel.append(sp2)
            elif sp2.upper().startswith('FOR_X'):
                gri_xd_spectel.append(sp2)
            else:
                gri_lwc_spectel.append(sp2)

        # INSTMODE updated from C2 to C2NC2 or NXCAC
        if skymode == 'C2NC2' and instmode != 'C2NC2':
            self.set_update('INSTMODE', instmode, 'C2NC2',
                            'Updating INSTMODE to match SKYMODE')
        elif skymode == 'NXCAC' and instmode != 'NXCAC':
            self.set_update('INSTMODE', instmode, 'NXCAC',
                            'Updating INSTMODE to match SKYMODE')

        # update SPECTEL2
        g6s = 'FOR_G329'
        if detchan == 1 and filt4_s == 'G6+blk' and spectel2 != g6s:
            self.set_update('SPECTEL2', spectel2, g6s,
                            'Updating SPECTEL2 to match FILT4_S')
            spectel2 = g6s

        # Fix instcfg for each mode
        mode = [
            {'instcfg': 'IMAGING_DUAL',
             'condit': (instmode in img_instmode and
                        slit in img_slit and
                        spectel1 in img_swc_spectel and
                        spectel2 in img_lwc_spectel and
                        dichroic in dual_dichroic),
             'datatype': 'IMAGE',
             'iconfig': 'IMAGING'},
            {'instcfg': 'GRISM_DUAL',
             'condit': (instmode in gri_instmode and
                        slit in gri_ls_slit and
                        spectel1 in gri_swc_spectel and
                        spectel2 in gri_lwc_spectel and
                        dichroic in dual_dichroic),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'IMAGING_SWC',
             'condit': (detchan == 0 and
                        instmode in img_instmode and
                        slit in img_slit and
                        spectel1 in img_swc_spectel and
                        dichroic in swc_dichroic),
             'datatype': 'IMAGE',
             'iconfig': 'IMAGING'},
            {'instcfg': 'IMAGING_LWC',
             'condit': (detchan == 1 and
                        instmode in img_instmode and
                        slit in img_slit and
                        spectel2 in img_lwc_spectel and
                        dichroic in lwc_dichroic),
             'datatype': 'IMAGE',
             'iconfig': 'IMAGING'},
            {'instcfg': 'GRISM_XD',
             'condit': (detchan == 0 and
                        instmode in gri_xd_instmode and
                        slit in gri_xd_slit and
                        spectel1 in gri_xd_spectel),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'GRISM_SWC',
             'condit': (detchan == 0 and
                        instmode in gri_instmode and
                        slit in gri_ls_slit and
                        spectel1 in gri_swc_spectel),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'GRISM_LWC',
             'condit': (detchan == 1 and
                        instmode in gri_instmode and
                        slit in gri_ls_slit and
                        spectel2 in gri_lwc_spectel),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'GRISM_XD_LSV',
             'condit': (detchan == 1 and
                        instmode in gri_instmode and
                        slit in gri_xd_slit and
                        spectel1 in gri_xd_spectel and
                        spectel2 in img_lwc_spectel),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'GRISM_SSV',
             'condit': (detchan == 1 and
                        instmode in gri_instmode and
                        slit in gri_ls_slit and
                        spectel1 in img_swc_spectel and
                        spectel2 in gri_lwc_spectel and
                        dichroic in dual_dichroic),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            {'instcfg': 'GRISM_LSV',
             'condit': (detchan == 1 and
                        instmode in gri_instmode and
                        slit in gri_ls_slit and
                        spectel1 in gri_swc_spectel and
                        spectel2 in img_lwc_spectel),
             'datatype': 'SPECTRAL',
             'iconfig': 'SPECTROSCOPY'},
            ]

        matched = False
        for mdict in mode:
            if mdict['condit']:
                matched = True
                if instcfg != mdict['instcfg']:
                    self.set_update('INSTCFG', instcfg, mdict['instcfg'],
                                    'Updating INSTCFG to match '
                                    'SPECTEL/SLIT/etc')
                    instcfg = mdict['instcfg']
                if datatype != mdict['datatype']:
                    self.set_update('DATATYPE', datatype, mdict['datatype'],
                                    'Updating DATATYPE to match '
                                    'SPECTEL/SLIT/etc')
                    datatype = mdict['datatype']
                if iconfig != mdict['iconfig']:
                    self.set_update('ICONFIG', iconfig, mdict['iconfig'],
                                    'Updating ICONFIG to match '
                                    'SPECTEL/SLIT/etc')
                    iconfig = mdict['iconfig']
                break

        if not matched:
            self.set_warning('INSTCFG', 'Instrument configuration not '
                             'recognized from SPECTEL/SLIT/etc')

        # Checks based on AOR ID
        if aor_id is None:
            # Fix AOR ID, if recorded as AOR-ID instead of AOR_ID
            aor_hyphen_id = self.read_value(header, 'AOR-ID')
            if aor_hyphen_id is not None:
                self.set_update('AOR_ID', aor_id, aor_hyphen_id,
                                'AOR_ID incorrectly changed to AOR-ID',
                                comment='Astronomical Observation '
                                'Request Identifier')
                self.set_update('AOR-ID', aor_hyphen_id, None,
                                'AOR_ID incorrectly changed to AOR-ID')
                aor_id = aor_hyphen_id
            else:
                # Fix missing AOR ID
                self.set_update('AOR_ID', aor_id, 'NONE',
                                'Missing AOR_ID',
                                comment='Astronomical Observation '
                                'Request Identifier')
                aor_id = 'NONE'
        else:
            # Fix OBSTYPE for standards, based on AOR ID
            if aor_id.startswith('90'):
                mccsmode = str(self.read_value(header,
                                               'MCCSMODE')).strip().upper()
                mccsmode = str(mccsmode).strip().upper()
                if datatype == 'IMAGE':
                    if mccsmode == 'FOR_LS' or mccsmode == 'FOR_SS':
                        if obstype != 'STANDARD_TELLURIC':
                            self.set_update('OBSTYPE', obstype,
                                            'STANDARD_TELLURIC',
                                            'Updating OBSTYPE to match AOR_ID')
                    elif obstype != 'STANDARD_FLUX':
                        self.set_update('OBSTYPE', obstype, 'STANDARD_FLUX',
                                        'Updating OBSTYPE to match AOR_ID')
                elif datatype == 'SPECTRAL' and obstype != 'STANDARD_TELLURIC':
                    self.set_update('OBSTYPE', obstype, 'STANDARD_TELLURIC',
                                    'Updating OBSTYPE to match AOR_ID')
            # Deferring fix for DATASRC
            # elif aor_id.startswith('84'):
            #     datasrc = self.read_value(header, 'DATASRC')
            #     if datasrc!='TEST':
            #         self.set_update('DATASRC', datasrc, 'TEST',
            #                             'Updating DATASRC to match AOR_ID')

            # Fix badly formed AOR IDs
            # Update the OBSTYPE and DATASRC to a default value
            # I set this to FLAT which is the most common but
            # add a message to warn the user to review the values
            if len(aor_id) < 4:
                self.set_update('AOR_ID', aor_id, 'NONE',
                                'Badly formed AOR_ID')
                aor_id = 'NONE'

        if aor_id == 'NONE':
            pass
            # Deferring fix for OBSTYPE
            # self.set_update('OBSTYPE', obstype, 'FLAT',
            #                 'Updating OBSTYPE to most common '
            #                 'for AOR_ID=NONE. '
            #                 'Set default to FLAT, verify observation log')

            # Deferring fix for DATASRC
            # self.set_update('DATASRC', datasrc, 'CALIBRATION',
            #                 'Updating DATASRC to most common '
            #                 'for AOR_ID=NONE. '
            #                 'Set default to CALIBRATION, verify '
            #                 'observation log')

        # Check CHPPROF/DTHPATT for underscores instead of hyphens
        chpprof = self.read_value(header, 'CHPPROF')
        if chpprof is not None and '_' in chpprof:
            self.set_update('CHPPROF', chpprof,
                            re.sub(r'_', '-', chpprof).upper(),
                            'Correcting format')
            self.unset_warning('CHPPROF')
        dthpatt = self.read_value(header, 'DTHPATT')
        if dthpatt is not None and '_' in dthpatt:
            self.set_update('DTHPATT', dthpatt,
                            re.sub(r'_', '-', dthpatt).upper(),
                            'Correcting format')
            self.unset_warning('DTHPATT')

        # Check CHPCDSYS: sky->ERF and array->SIRF
        chpcrsys = self.read_value(header, 'CHPCRSYS')
        if chpcrsys == 'sky':
            self.set_update('CHPCRSYS', chpcrsys,
                            'ERF',
                            'Correcting value')
            self.unset_warning('CHPCRSYS')
        if chpcrsys == 'array':
            self.set_update('CHPCRSYS', chpcrsys,
                            'SIRF',
                            'Correcting value')
            self.unset_warning('CHPCRSYS')

        # Check WCS keywords
        ctype1 = self.read_value(header, 'CTYPE1')
        ctype2 = self.read_value(header, 'CTYPE2')
        radesys = self.read_value(header, 'RADESYS')
        equinox = self.read_value(header, 'EQUINOX')
        if ctype1 is not None and ctype1 != 'RA---TAN':
            self.set_update('CTYPE1', ctype1, 'RA---TAN',
                            'Correcting to known value')
        if ctype2 is not None and ctype2 != 'DEC--TAN':
            self.set_update('CTYPE2', ctype2, 'DEC--TAN',
                            'Correcting to known value')
        if radesys is not None and str(radesys) != 'FK5':
            self.set_warning('RADESYS', 'ERROR: RADESYS ' + str(radesys) +
                             ' != FK5; possible problem with WCS')
        if equinox is not None and str(equinox) != '2000':
            self.set_warning('EQUINOX', 'ERROR: EQUINOX ' + str(equinox) +
                             ' != 2000; possible problem with WCS')

        # As of 9/11/15, Flight 238, FORCAST mistakenly converted
        # TELRA to decimal degrees in raw files.  Convert it back.
        # Should be fixed for flight 254 and later
        telra = self.read_value(header, 'TELRA')
        missn_id = str(self.read_value(header, 'MISSN-ID'))
        mid = re.match('.*_F(\d{3,4})$', missn_id)
        try:
            mnbr = int(mid.group(1))
        except:
            mnbr = 0
        if telra is not None and (mid and mnbr >= 238 and mnbr < 254):
            self.set_update('TELRA', telra, telra/15.0,
                            'Fixing TELRA from decimal degrees to hours')
            # set it in the current header so that it is used properly
            # during wcs checks
            header['TELRA'] = telra/15.0

        # Check WCS values for consistency
        self.wcs_check(header)

        # Check FILT1_S for unreadable character
        filt1_s = self.read_value(header, 'FILT1_S')
        if filt1_s is not None:
            # Strip out any single-quotes -- the archive
            # can't ingest files with keywords like
            #   FILT1_S = '    N''
            if str(filt1_s).strip().upper() == "N'":
                filt1_s = 'Nprime'
            else:
                filt1_s = re.sub(r"'", '', filt1_s)
            old = header['FILT1_S']
            try:
                old = old.decode('ascii')
            except UnicodeDecodeError:
                old = '(unreadable)'.decode('ascii')
            if filt1_s != old:
                self.set_update('FILT1_S', old, filt1_s, 'Fixing formatting')

        # Check for empty keywords that should be set to UNKNOWN
        tracmode = self.read_value(header, 'TRACMODE')
        if tracmode is None or tracmode.strip() == '':
            self.set_update('TRACMODE', tracmode, 'UNKNOWN',
                            'Fixing blank entry')
        telequi = self.read_value(header, 'TELEQUI')
        if telequi is None or telequi.strip() == '':
            self.set_update('TELEQUI', telequi, 'UNKNOWN',
                            'Fixing blank entry')
        lastrew = self.read_value(header, 'LASTREW')
        if lastrew is None or lastrew.strip() == '':
            self.set_update('LASTREW', lastrew, 'UNKNOWN',
                            'Fixing blank entry')

        # Correct DITHERCS integers to strings
        # And fix to newer keyword name
        dithercs = self.read_value(header, 'DITHERCS')
        dthrcs = self.read_value(header, 'DTHRCS')
        dthcrsys = self.read_value(header, 'DTHCRSYS')
        csval = None
        if dithercs is not None:
            if str(dithercs).strip()=='2':
                csval = 'ERF'
            elif str(dithercs).strip()=='0':
                csval = 'SIRF'
            elif str(dithercs).strip()=='1':
                csval = 'TARF'
            else:
                csval = dithercs
            self.set_update('DITHERCS', dithercs, None,
                            'Fixing old-style dither coordinate system')
        if dthrcs is not None:
            csval = dthrcs
            self.set_update('DTHRCS', dthrcs, None,
                            'Fixing old-style dither coordinate '
                            'system keyword')
        if dthcrsys is None and csval is not None:
            self.set_update('DTHCRSYS', dthcrsys, csval,
                            'Fixing old-style dither coordinate '
                            'system keyword')

        # Warn about some unfixable things
        chpsetl = self.read_value(header, 'CHPSETL')
        object_h = self.read_value(header, 'OBJECT')
        ditherx = self.read_value(header, 'DITHERX')
        dithery = self.read_value(header, 'DITHERY')
        if chpsetl is not None and chpsetl < 23:
            self.set_warning('CHPSETL', 'ERROR: '+str(chpsetl)+' <23ms')
        if (object_h is None or str(object_h).upper() == 'UNKNOWN' or
            len(object_h) < 2):
            self.set_warning('OBJECT', 'ERROR: set to ' + str(object_h))
        if ditherx == -9999:
            self.set_warning('DITHERX', 'ERROR: set to ' + str(ditherx))
        if dithery == -9999:
            self.set_warning('DITHERY', 'ERROR: set to ' + str(dithery))

        # Special treatment for the NLINSLEV keyword, to split
        # a string array into 4 floats
        nlinslev = self.read_value(header, 'NLINSLEV')
        if nlinslev is not None:
            bglev = nlinslev.split(',')
            try:
                bglev = [float(bgl.strip('[]')) for bgl in bglev]
            except ValueError:
                bglev = []
            for i in range(len(bglev)):
                self.key_values['BGLEVEL'+str(i+1)] = bglev[i]

        # Check for test file that is not caught by a weird ZA
        # (as in sofia_rules)
        za_start = self.read_value(header, 'ZA_START')
        skymode = self.read_value(header, 'SKYMODE')
        chpangle = self.read_value(header, 'CHPANGLE')
        if ((za_start is None or za_start == -9999) and
                (skymode is None or skymode == 'UNKNOWN') and
                (chpangle is None or chpangle == -9999)):
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Excluding test file')

        # Check for Flow data
        flowrel = str(self.read_value(header, 'FLOWREL')).strip().upper()
        if flowrel == 'TRUE' or flowrel == 'T':
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Excluding FLOW file')

        # Check for and fix 'UNKNOWN' value in UTCSTART
        dateobs = self.read_value(header, 'DATE-OBS')
        utcstart = self.read_value(header, 'UTCSTART')
        blank_val = ['NONE', 'UNKNOWN']
        if (str(utcstart).strip().upper() in blank_val and
                str(dateobs).strip().upper not in blank_val):
            starttime = str(dateobs).split('T')
            if len(starttime) == 2:
                self.set_update('UTCSTART', utcstart, starttime[1],
                                'Setting UTCSTART from DATE-OBS')

    def wcs_check(self, header):
        """Check whether WCS keywords are consistent"""

        # Function to set warning message if necessary
        def set_msg(keys):
            msg = 'ERROR: incomplete WCS information in header '
            msg += '(keys: ' + ','.join(keys) + ')'
            self.set_warning('OBSDIF1', msg)
            self.set_warning('OBSDIF2', msg)

        # Set WCSQUAL to unknown by default
        self.set_update('WCSQUAL', None, 'UNKNOWN',
                        'WCS quality unknown')

        # WCS information
        nodamp = self.read_value(header, 'NODAMP')
        nodangle = self.read_value(header, 'NODANGLE')
        chpamp = self.read_value(header, 'CHPAMP1')
        chpangle = self.read_value(header, 'CHPANGLE')
        ditherx = self.read_value(header, 'DITHERX')
        dithery = self.read_value(header, 'DITHERY')
        dithercs = self.read_value(header, 'DITHERCS')
        dthcrsys = self.read_value(header, 'DTHCRSYS')
        skyangl = self.read_value(header, 'SKY_ANGL')
        if dthcrsys is not None:
            dithercs = dthcrsys
        obsra = self.read_value(header, 'OBSRA')
        obsdec = self.read_value(header, 'OBSDEC')
        crval1 = self.read_value(header, 'CRVAL1')
        crval2 = self.read_value(header, 'CRVAL2')
        pixscale = 0.768
        
        if None in [obsra, obsdec, crval1, crval2]:
            set_msg(['obsra', 'obsdec', 'crval1', 'crval2'])
            return
        if None in [nodamp, nodangle, chpamp, chpangle, skyangl]:
            set_msg(['nodamp', 'nodangle', 'chpamp1', 'chpangle', 'sky_angl'])
            return

        # Convert dither amplitudes to arcsec
        if dithercs not in [None, 0, 2, 'ERF', 'SIRF']:
            set_msg(['dithercs'])
            return
        if ditherx is None:
            ditherx = 0.0
        if dithery is None:
            dithery = 0.0

        # If Flight number <= 333, then
        # obsra is in degrees.  If later, then in decimal hours.
        missn_id = str(self.read_value(header, 'MISSN-ID'))
        mid = re.match('.*_F(\d{3,4})$', missn_id)
        try:
            mnbr = int(mid.group(1))
        except:
            mnbr = 0
        if mnbr > 333:
            obsra *= 15.0
        
        # Diff between observed RA/Dec and CRVALs
        obsdif1 = ((obsra - crval1) * \
                   np.cos(np.deg2rad(obsdec))) * 3600.
        obsdif2 = (obsdec - crval2) * 3600.
        if str(dithercs) == 'ERF' or str(dithercs) == '2':
            obsdif1 += ditherx
            obsdif2 += dithery
        elif str(dithercs) == 'SIRF' or str(dithercs) == '0':
            # project dither onto sky coordinates
            skyrad = np.deg2rad(180. - skyangl)
            proj_dithx = -1 * pixscale * (ditherx * np.cos(skyrad) +
                                          dithery * np.sin(skyrad))
            proj_dithy = pixscale * (-1 * ditherx * np.sin(skyrad) +
                                     dithery * np.cos(skyrad))
            obsdif1 += proj_dithx
            obsdif2 += proj_dithy

        # Set warning for large diffs
        # (accuracy of one FORCAST pixel 0.768)
        warn_keys = []
        if np.abs(obsdif1) > pixscale:
            self.set_warning('OBSDIF1',
                             'OBSRA - CRVAL1 + DITHERX '
                             'is greater than +-%.3f' % pixscale)
            header['OBSDIF1'] = obsdif1
            warn_keys.append('OBSDIF1')
        if np.abs(obsdif2) > pixscale:
            self.set_warning('OBSDIF2',
                             'OBSDEC - CRVAL2 + DITHERY '
                             'is greater than +-%.3f' % pixscale)
            header['OBSDIF2'] = obsdif2
            warn_keys.append('OBSDIF2')

        # Set calculated values as updates
        keys = ['OBSDIF1', 'OBSDIF2']
        vals = [obsdif1, obsdif2]
        comments = ['OBSRA - CRVAL1 (arcsec)',
                    'OBSDEC - CRVAL2 (arcsec)']
        for cidx in range(len(keys)):
            if keys[cidx] in warn_keys:
                continue
            self.set_update(keys[cidx], None, vals[cidx], comments[cidx])

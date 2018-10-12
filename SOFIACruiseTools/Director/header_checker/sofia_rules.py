"""General header validation methods."""

from __future__ import print_function

import os
import re
import json
from pydoc import locate

try:
    import astropy.io.fits as pf
except ImportError:
    import pyfits as pf
import xmltodict

from.pyqa_utils import CaptureOutput


class SOFIARules(object):

    """Parent class for any SOFIA instrument checks."""

    def __init__(self, dictfile=None, kwdict=None):

        self.name = 'SOFIA'
        self.condition = ['*']
        self.required_keys = []
        self.ignore_keys = ['COMMENT', 'HISTORY']
        self.exclude_keys = []
        self.update_keys = []

        self.app_path = os.path.dirname(os.path.realpath(__file__)) + \
            os.path.sep

        # Read preferred display keys
        keyfile = self.app_path+'keyword_dicts/DCS/SOFIA_keys.json'
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

        # Read SOFIA rules
        self.keyword_dict = self.read_keyword_dict(dictfile=dictfile,
                                                   kwdict=kwdict)

        self.fullname = ''
        self.basename = ''
        self.updates = {}
        self.warnings = {}
        self.key_values = {}

    def read_value(self, header, key):
        """Read value from header if present, return None if not."""
        try:
            try:
                value = header[key]
            except KeyError:
                value = None
            if type(value) is str:
                value = value.decode('ascii', 'ignore')
            return value
        except:
            return None

    def set_update(self, key, old, new, note, comment=None, dtype=None):
        """Set an update message in the updates dictionary."""
        update = {'old': old,
                  'new': new,
                  'note': note,
                  'type': dtype,
                  'comment': comment}
        self.updates[key] = update

    def set_warning(self, key, note, append=False):
        """Set a warning message in the warnings dictionary."""
        if append:
            if key in self.warnings:
                self.warnings[key] += '; '+note
            else:
                self.warnings[key] = note
        else:
            self.warnings[key] = note

    def unset_update(self, key):
        """Remove an update message."""
        if type(key) is not list:
            key = [key]
        for k in key:
            try:
                del self.updates[k]
            except KeyError:
                pass

    def unset_warning(self, key):
        """Remove a warning message."""
        if type(key) is not list:
            key = [key]
        for k in key:
            try:
                del self.warnings[k]
            except KeyError:
                pass

    def read_keyword_dict(self, dictfile=None, kwdict=None):
        """Parse the keyword dictionary definition file."""

        if kwdict is not None:
            dictfile = None
        if kwdict is None and dictfile is None:
            dictfile = self.app_path + 'keyword_dicts/DCS/KWDict_working.xml'

        if kwdict is None:
            if not os.path.exists(dictfile):
                raise IOError('Dictionary file {0} does not '
                              'exist'.format(dictfile))

            kwdict = {}
            basename = os.path.basename(dictfile).lower()
            if basename.endswith('.xml'):

                with open(dictfile, 'rb') as dfile:
                    fulldict = xmltodict.parse(dfile)

                    for klist in fulldict['KeywordDictionary']['KeywordList']:
                        for kwd in klist['Keyword']:
                            try:
                                req = kwd['Requirement']
                                try:
                                    req = kwd['Requirement']['@condition']
                                except KeyError:
                                    req = '*'
                            except KeyError:
                                req = None
                            try:
                                fits = kwd['FITS']
                                if type(fits) is list:
                                    name = fits[0]['@name']
                                    dtype = [f['@type'] for f in fits]
                                else:
                                    name = fits['@name']
                                    dtype = [fits['@type']]
                            except KeyError:
                                name = None
                                dtype = None

                            try:
                                value = kwd['Value']
                                if type(value) is list:
                                    drange = [
                                        {'type': v['Range']['@type'],
                                         'value': v['Range']['#text'],
                                         'representation':
                                             v['@representation']}
                                        for v in value]
                                else:
                                    drange = [{'type': value['Range']['@type'],
                                               'value':
                                                   value['Range']['#text'],
                                               'representation':
                                                   value['@representation']}]
                            except KeyError:
                                drange = None

                            if name is not None:
                                name = re.sub(r'\%?\d?[a-z]', r'\d+', name)
                                name = str(name).strip()
                                kwdict[name] = {'dtype': dtype,
                                                'drange': drange,
                                                'requirement': req}

            elif basename.endswith('.json'):

                with open(dictfile) as dfile:
                    try:
                        kwdict = json.load(dfile)
                    except ValueError:
                        raise IOError('Invalid JSON code in '+dictfile)

            else:
                raise IOError('Dictionary file '+dictfile+' must be '
                              'XML or JSON (.xml, .json).')

        for key in kwdict:
            req = kwdict[key]['requirement']
            if req is not None and \
                    req in self.condition and \
                    key not in self.required_keys:
                self.required_keys.append(key)

        return kwdict

    def check_value(self, value, dtype, drange, allow_missing=False):
        """Check a value against the requirements for the keyword."""

        # Check type
        vtype = type(value)
        if isinstance(dtype,list):
            dtype = dtype[0]
            
        wrong_type = 'Wrong type: '+str(vtype)+', should be '+str(dtype)
        if dtype and len(dtype) > 0:
            if isinstance(value, bool):
                try:
                    idx = dtype.index('log')
                except ValueError:
                    try:
                        idx = dtype.index('bool')
                    except:
                        return wrong_type
            elif isinstance(value,int):
                try:
                    idx = dtype.index('int')
                except ValueError:
                    try:
                        idx = dtype.index('flt')
                    except ValueError:
                        return wrong_type
            elif isinstance(value, float):
                try:
                    idx = dtype.index('flt')
                except ValueError:
                    return wrong_type
            elif isinstance(value, str):
                try:
                    idx = dtype.index('str')
                except ValueError:
                    return wrong_type
            else:
                return wrong_type

        # Check value
        wrong_value = 'Wrong value: '+str(value)+', should be '
        missing_num = -9999
        missing_str = 'UNKNOWN'
        if drange is not None:
            drange = drange[idx]
            # if vtype in [int, long, float] and not \
            if isinstance(vtype, (int, float)) and not \
                    (allow_missing and value == missing_num):
                if drange['type'] == 'interval':
                    try:
                        low, high = drange['value'].split(',')
                        low = float(low)
                        high = float(high)
                    except (ValueError, IndexError):
                        return 'Bad range definition: interval ' + \
                            drange['value']
                    if value < low or value > high:
                        return wrong_value + 'within [' + drange['value'] + ']'
                elif drange['type'] == 'gt':
                    try:
                        low = float(drange['value'])
                    except ValueError:
                        return 'Bad range definition: gt ' + \
                            drange['value']
                    if value < low:
                        return wrong_value + 'greater than ' + drange['value']
                elif drange['type'] == 'lt':
                    try:
                        high = float(drange['value'])
                    except ValueError:
                        return 'Bad range definition: lt ' + \
                            drange['value']
                    if value > high:
                        return wrong_value + 'less than '+drange['value']
                elif drange['type'] == 'eq':
                    try:
                        val = float(drange['value'])
                    except ValueError:
                        return 'Bad range definition: eq ' + \
                            drange['value']
                    if value != val:
                        return wrong_value + 'equal to ' + drange['value']
                elif drange['type'] == 'enum':
                    enum = drange['value'].split(',')
                    enumchk = [value == float(e) for e in enum]
                    if True not in enumchk:
                        return wrong_value + 'within ['+drange['value']+']'
            elif (vtype is str and not
                  (allow_missing and value == missing_str)):
                if drange['type'] == 'enum':
                    enum = drange['value'].split(',')
                    enum = [e.strip().lower() for e in enum]
                    if value.strip().lower() not in enum:
                        return wrong_value + 'within ['+drange['value']+']'
        return None

    def add_mode_reqs(self, header):
        """Add some extra requirements by observation mode."""

        try:
            nodding = header['NODDING']
            if type(nodding) is not bool:
                if str(nodding).upper() == 'TRUE':
                    nodding = True
                else:
                    nodding = False
        except KeyError:
            nodding = False
        try:
            chopping = header['CHOPPING']
            if type(chopping) is not bool:
                if str(chopping).upper() == 'TRUE':
                    chopping = True
                else:
                    chopping = False
        except KeyError:
            chopping = False
        try:
            scanning = header['SCANNING']
            if type(scanning) is not bool:
                if str(scanning).upper() == 'TRUE':
                    scanning = True
                else:
                    scanning = False
        except KeyError:
            scanning = False
        try:
            mapping = header['MAPPING']
            if type(mapping) is not bool:
                if str(mapping).upper() == 'TRUE':
                    mapping = True
                else:
                    mapping = False
        except KeyError:
            mapping = False
        try:
            dithering = header['DITHER']
            if type(dithering) is not bool:
                if str(dithering).upper() == 'TRUE':
                    dithering = True
                else:
                    dithering = False
        except KeyError:
            dithering = False
        try:
            imaging = (header['DATATYPE'].upper() == 'IMAGE')
        except (KeyError, TypeError):
            imaging = False
        try:
            spectroscopy = (header['DATATYPE'].upper() == 'SPECTRAL')
        except (KeyError, TypeError):
            spectroscopy = False
        try:
            lissajous = scanning and (header['SCNPATT'].upper() == 'LISSAJOUS')
        except (KeyError, TypeError):
            lissajous = False
        try:
            raster = scanning and (header['SCNPATT'].upper() == 'RASTER')
        except (KeyError, TypeError):
            raster = False
        try:
            sweep =  scanning and (header['SCNPATT'].upper() == 'SWEEP')
        except (KeyError, TypeError):
            if scanning and not lissajous and not raster:
                sweep = True
            else:
                sweep = False

        for key in self.keyword_dict:
            req = self.keyword_dict[key]['requirement']
            if req is None:
                continue
            req = req.lower()
            condit = ((nodding and 'nodding' in req) or
                      (chopping and 'chopping' in req) or
                      (scanning and 'scanning' in req) or
                      (mapping and 'mapping' in req) or
                      (dithering and 'dithering' in req) or
                      (imaging and 'imaging' in req) or
                      (spectroscopy and 'spectroscopy' in req) or
                      (lissajous and 'lissajous scan' in req) or
                      (raster and 'raster scan' in req) or
                      (sweep and 'sweep scan' in req))
            if condit:
                self.required_keys.append(key)

    def check_header(self, header):
        """Perform all required keyword checks on the header."""

        self.add_mode_reqs(header)

        for key in self.required_keys:
            if key in self.ignore_keys:
                continue

            if key in header:
                matches = [key]
                value = [header[key]]
            else:
                matches = []
                value = []
                for k in header.keys():
                    if re.match('^' + key + '$', k):
                        matches.append(k)
                        value.append(header[k])
            n_matches = len(matches)
            if n_matches > 0:
                kw_elem = self.keyword_dict[key]

                for i in range(n_matches):
                    key = matches[i]
                    val = value[i]
                    msg = self.check_value(val, kw_elem['dtype'],
                                           kw_elem['drange'])
                    if msg is not None:
                        self.set_warning(key, msg)

            else:
                self.set_warning(key, 'Not present')

        # Custom checks for particular keywords
        # not well described in the dictionary
        # -------------------------------------

        # Check for filename mismatch
        filename = self.read_value(header, 'FILENAME')
        if filename != self.basename:
            self.set_update('FILENAME', filename, self.basename,
                            'Updating FILENAME to match actual filename')

        # Check for imaging WCS keywords: either CDi_j or CDELTn/CROTA2
        # may be present; no need to warn if the other is missing
        wkeys = self.warnings.keys()
        if r'CD\d+_\d+' in wkeys:
            if 'CROTA2' not in wkeys and r'CDELT\d+' not in wkeys:
                self.unset_warning(r'CD\d+_\d+')
        if 'CROTA2' in wkeys or r'CDELT\d+' in wkeys:
            if r'CD\d+_\d+' not in wkeys:
                self.unset_warning(['CROTA2', r'CDELT\d+'])

        # Check for MISSN-ID and if it is unknown then set warning
        missnid = self.read_value(header, 'MISSN-ID')
        if str(missnid).upper() == 'UNKNOWN':
            self.set_warning('MISSN-ID', 'MISSN-ID is set as UNKNOWN')

        # Check for invalid LASTREW value
        lastrew = self.read_value(header, 'LASTREW')
        if lastrew is not None and str(lastrew) != 'UNKNOWN':
            if not re.match('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3}Z)?',
                            lastrew):
                self.set_update('LASTREW', lastrew, 'UNKNOWN',
                                'Fixing bad value')

        # Check for bad ZA value (usually a test file)
        # and for possible vignetting
        za_start = self.read_value(header, 'ZA_START')
        za_end = self.read_value(header, 'ZA_END')
        if za_start is not None and za_start != -9999:
            # exclude if ZA too high or too low
            if za_start > 80 or za_start < 0:
                self.set_update('EXCLUDE', None, 'TRUE',
                                'Excluding test file (ZA=%.2f)' % za_start)
            lat_sta = self.read_value(header, 'LAT_STA')
            if lat_sta is None or lat_sta != -9999:
                min_za = 33
                max_za = 67
            elif lat_sta < 0:
                min_za = 33
                max_za = 69
            else:
                min_za = 31
                max_za = 67
            if (za_start < min_za or za_start > max_za):
                self.set_warning('ZA_START',
                                 'Possible vignetting (ZA<%.1f ' % min_za+
                                 'or ZA>%.1f).' % max_za)
            if (za_end < min_za or za_end > max_za):
                self.set_warning('ZA_END',
                                 'Possible vignetting (ZA<%.1f ' % min_za+
                                 'or ZA>%.1f).' % max_za)
        else:
            # also exclude if ZA missing
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Excluding test file (missing ZA)')

        # Check DATE-OBS formatting
        dateobs = self.read_value(header, 'DATE-OBS')
        if dateobs is not None:
            if not re.match('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$',
                            dateobs):
                self.set_warning('DATE-OBS', 'Badly formatted date')

        # Check PLANID, fix based on AOR ID if possible
        aor_id = self.read_value(header, 'AOR_ID')
        planid = self.read_value(header, 'PLANID')
        if (aor_id is not None and
                len(str(aor_id)) >= 7 and
                re.match('^\d{2}_\d{4}_\d+$', str(aor_id))):
            if planid != aor_id[0:7]:
                self.set_update('PLANID', planid, aor_id[0:7],
                                'Updating PLANID to match AOR_ID')

        # Check for PROCSTAT, fix if blank
        procstat = self.read_value(header, 'PROCSTAT')
        if procstat is None or not str(procstat).upper().startswith('LEVEL'):
            self.set_update('PROCSTAT', procstat, 'LEVEL_1',
                            'Fixing bad PROCSTAT value')

    def check(self, fname, skip_checks=False, verbose=False):
        """Open the file and perform the validation."""

        if not os.path.exists(fname):
            raise IOError('Input file '+fname+' does not exist')

        self.fullname = os.path.abspath(fname)
        self.basename = os.path.basename(fname)
        if not self.basename.endswith('.fits'):
            raise TypeError('Input file '+fname+' is not FITS')

        try:
            with CaptureOutput() as output:
                hdul = pf.open(fname)
                hdul.verify('exception')
            if len(output) > 0:
                msg = ''
                for line in output:
                    msg += '  '+line.strip()+'\n'
                raise IOError(msg)
        except Exception as err:
            #msg = err.message
            msg = err.args[0]
            print(err.args)
            msg = msg.decode('ascii', 'ignore')
            if verbose:
                print( 'WARNING from pyfits:' )
                print( '  '+msg.strip()) 

            msg = re.sub(r'\s+', ' ', msg)
            self.set_warning('SIMPLE', 'Invalid FITS: ' + msg)
            self.set_update('EXCLUDE', None, 'TRUE',
                            'Bad FITS file')

            # Check for zero-length file
            try:
                if os.stat(self.fullname).st_size == 0:
                    self.set_update('REMOVE', None, 'TRUE',
                                    'Zero-length file')
            except OSError:
                pass
                    
            with CaptureOutput() as output:
                hdul = pf.open(fname, ignore_missing_end=True)
                try:
                    hdul.verify('silentfix')
                except (ValueError, pf.verify.VerifyError):
                    # nothing else to try
                    hdul = []

        if len(hdul) > 0:
            # Check for warnings and updates, read key values
            self.check_header(hdul[0].header)
        if skip_checks:
            self.updates = {}
            self.warnings = {}

        if verbose and not skip_checks:
            n_warn = len(self.warnings)
            n_update = len(self.updates)

            if n_warn == 0 and n_update == 0:
                print('\nHeader passed all checks.')
            if n_warn > 0:
                print('\nWarnings:')
                for wstr, mstr in self.warnings.iteritems():
                    print('  ' + wstr + ': ' + mstr)
            if n_update > 0:
                print('\nUpdates:')
                for wstr, mstr in self.updates.iteritems():
                    print('{0:s}: From {1:s} to {2:s}. {3:s}.'.format(
                            wstr, str(mstr['old']), str(mstr['new']), 
                            str(mstr['note'])))
            print('')

        # Read required/preferred/updated key values from header
        full_keys = list(self.updates.keys()) + list(self.warnings.keys())
        # for key in self.updates.keys() + self.warnings.keys():
        for key in full_keys:
            self.preferred_keys.add(key)
        if len(hdul) > 0:
            all_keys = set(list(self.preferred_keys) + 
                           list(hdul[0].header.keys()))
            for key in all_keys:
                if key in self.ignore_keys or key in self.key_values:
                    continue
                val = self.read_value(hdul[0].header, key)
                self.key_values[key] = val

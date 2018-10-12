
"""Utility functions, for use with header_checker."""

import os
import re
import sys
try:
    import cStringIO
except ModuleNotFoundError:
    import io as cStringIO
import glob
import fnmatch
import math
import subprocess
try:
    import astropy.io.fits as pf
except ImportError:
    import pyfits as pf


class CaptureOutput(list):
    """Class to capture stdout and stderr output."""
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stringio = cStringIO.StringIO()
        sys.stdout = self._stringio
        sys.stderr = self._stringio
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout
        sys.stderr = self._stderr


def find_fits_files(filepath, recurse=False):
    """Recurse a filepath, finding all FITS files."""

    if type(filepath) is not list:
        filepath = [filepath]

    fits = []
    for fpth in filepath:
        flist = glob.glob(fpth)
        for fnm in flist:
            if os.path.isdir(fnm):
                if recurse:
                    for root, dirnames, filenames in os.walk(fnm):
                        for sfnm in fnmatch.filter(filenames, '*.fits'):
                            fitsfile = os.path.join(root, sfnm)
                            fits.append(fitsfile)
                else:
                    fits += glob.glob(fnm+'/*.fits')
            elif os.path.isfile(fnm):
                if fnm.endswith('.fits'):
                    fits.append(fnm)
    return fits


def natural_sort(ulist):
    """Sort a list, treating numbers naturally (so 9 comes before 10)"""
    slist = [str(u) for u in ulist]
    get_int = lambda s: int(s) if s.isdigit() else s.upper()
    split_alphanum = lambda s: [get_int(c) for c in re.split('(\d+)', s)]
    return sorted(slist, key=split_alphanum)


def history_default(obj):
    """Return values for types that can't be directly dumped to JSON"""
    if isinstance(obj, pf.header._HeaderCommentaryCards):
        return str(obj)
    if isinstance(obj, pf.card.Undefined):
        return None
    raise TypeError('Unparseable JSON type: %s' % type(obj))

def get_version():
    try:
        cur_dir = os.getcwd()
        git_dir = os.path.dirname(__file__)
        os.chdir(git_dir)
        try:
            with open(os.devnull, 'w') as devnull:
                version = subprocess.check_output(['git', 'describe',
                                                   '--always', 'HEAD'],
                                                  stderr=devnull).strip()
        except Exception:
            version = 'UNKNOWN'
        os.chdir(cur_dir)
    except OSError:
        version = 'UNKNOWN'
    return 'SOFIA QA Tools, version %s' % str(version)

def round_to_n(x, n):
    if x == 0:
        return x
    neg = False
    if x < 0:
        x *= -1.0
        neg = True
    val = round(x, -int(math.floor(math.log10(x))) + (n - 1))
    if neg: val *= -1.0
    return val

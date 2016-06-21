# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:21:44 2016

@author: rhamilton
"""

import re
import sys
import copy
import itertools
import numpy as np
import scipy.interpolate as spi
from datetime import datetime, timedelta


class nonsiderial(object):
    """
    Keeping all the non-siderial object info in a helpful place.
    """
    def __init__(self):
        self.peridist = 0.
        self.ecc = 0.
        self.incl = 0.
        self.argperi = 0.
        self.longascnode = 0.
        self.perijd = 0.
        self.epochjd = 0.


class flightprofile(object):
    """
    Defining several common flight plan ... thingies.
    """
    def __init__(self):
        self.filename = ''
        self.saved = ''
        self.origin = ''
        self.destination = ''
        self.takeoff = 0
        self.landing = 0
        self.obstime = 0
        self.flighttime = 0
        # In a perfect world, I'd just make this be len(legs)
        self.nlegs = 0
        self.legs = []

    def add_leg(self, parsedleg):
        self.legs.append(parsedleg)

    def flatprofile(self, epoch=datetime(1970, 1, 1)):
        time, lat, lon, mhdg, thdg = [], [], [], [], []
        for each in self.legs:
            time.append(each.relative_time)
            lat.append(each.lat)
            lon.append(each.long)
            mhdg.append(each.mhdg)
            thdg.append(each.thdg)

        # Actually flatten those lists
        time = list(itertools.chain.from_iterable(time))
        lat = list(itertools.chain.from_iterable(lat))
        lon = list(itertools.chain.from_iterable(lon))
        mhdg = list(itertools.chain.from_iterable(mhdg))
        thdg = list(itertools.chain.from_iterable(thdg))

        return time, lat, lon, mhdg, thdg


class legprofile(object):
    """
    Defining several common leg characteristics, to be imbedded inside a
    flightprofile object for easy access.
    """

    def __init__(self):
        self.legtype = ''
        self.target = ''
        self.nonsiderial = False
        self.start = ''
        self.duration = ''
        self.altitude = ''
        self.ra = ''
        self.dec = ''
        self.epoch = ''
        self.range_elev = []
        self.range_rof = []
        self.range_rofrt = []
        self.moonangle = 0
        self.utc = []
        self.utcdt = []
        self.elapsedtime = []
        self.mhdg = []
        self.thdg = []
        self.lat = []
        self.long = []
        self.wind_dir = []
        self.wind_speed = []
        self.temp = []
        self.lst = []
        self.elev = []
        self.relative_time = []
        self.rof = []
        self.rofrt = []
        self.loswv = []
        self.sunelev = []
        self.comments = []


go_dt = lambda x: timedelta(seconds=x)
go_iso = lambda x: x.isoformat()


def findLegHeaders(words, header):
    """
    Given a file (already opened and read via readlines()),
    return the line number locations where the given header lines occur.
    """
    locs = []
    for i, line in enumerate(words):
        match = header.match(line)
        if match is not None:
            locs.append(i)

    return locs


def keyValuePair(line, key, delim=":", dtype=None, linelen=None):
    """
    Given a line and a key supposedly occuring on that line, return its
    value in the given dtype (if dtype is not None).  If the value isn't
    found, or there's an error, return None.

    Assumes that the value has no spaces in it
    """
    # Search for the keyword in the line
    loc = line.strip().lower().find(key.lower())
    if loc == -1:
        val = None
    else:
        # Split on the ':' following the keyword
        try:
            val = line[loc:].strip().split(":")[1].split()[0].strip()
        except:
            val = None
    if dtype is int:
        try:
            val = np.int(val)
        except:
            val = val
    elif dtype is float:
        try:
            val = np.float(val)
        except:
            val = val

    return val


def keyValuePairDT(line, key, delim=":", length=24):
    """
    Given a line and a key supposedly occuring on that line, return its
    value and turn it into a datetime object.  Need a seperate function since
    the parsing rule has to be a bit more customized to get all the parts.
    """
    # Search for the keyword in the line
    loc = line.strip().lower().find(key.lower())
    if loc == -1:
        val = None
    else:
        # Split on the ':' following the keyword
        try:
            val = ':'.join(line[loc:].split(":")[1:]).strip()[:length]
        except:
            val = None

    dtobj = datetime.strptime(val, "%Y-%b-%d %H:%M:%S %Z")
    return dtobj


def legHeaderPuller(headerstart, headerend):
    """
    Given the starting location of the first line of a header and the
    starting location of the leg data, parse all the crap in between that's
    important and useful and return the leg class for further use.
    """
    print "Leg metadata between lines %d and %d" % (headerstart, headerend)


def parseMIS(infile):
    """
    Read a SOFIA .MIS file, parse it, and return a nice thing we can work with
    """
    # Create an empty base class that we'll fill up as we read through
    flight = flightprofile()

    # Read the file into memory so we can quickly parse stuff
    f = open(infile, 'r')
    contents = f.readlines()
    f.close()

    # First line of the file is usually the filename and time it was made
    firstsplit = ['Filename', 'Saved']
    flight.filename = keyValuePair(contents[0], firstsplit[0])
    flight.saved = keyValuePairDT(contents[0], firstsplit[1])

    # Search for the header lines which will tell us how many legs there are.
    #  Use a regular expression to make the searching less awful
    head1 = "Leg \d* \(.*\)"
    legheads = findLegHeaders(contents, re.compile(head1))
    flight.nlegs = len(legheads)

    head2 = "UTC\s*MHdg"
    legdatas = findLegHeaders(contents, re.compile(head2))

    if len(legdatas) != len(legheads):
        print "FATAL ERROR: Couldn't find the same amount of legs and data!"
        print "Check the formatting of the file?"
        print "Looking for '%s' and '%s'" % (head1, head2)
        return -1

    for i, datastart in enumerate(legheads):
        legHeaderPuller(legheads[i], legdatas[i])


if __name__ == "__main__":
    infile = '201509_FO_04_Wx12.mis'
    parseMIS(infile)

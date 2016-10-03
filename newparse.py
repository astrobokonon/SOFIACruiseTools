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


go_dt = lambda x: timedelta(seconds=x)
go_iso = lambda x: x.isoformat()


def findLegHeaders(words, header, how='match'):
    """
    Given a file (already opened and read via readlines()),
    return the line number locations where the given header lines occur.

    Use the 'how' keyword to control the searching;
        header.match() checks the BEGINNING of the words string only
    """
    locs = []
    for i, line in enumerate(words):
        match = header.match(line)
        if match is not None:
            locs.append(i)

    return locs


def keyValuePair(line, key, delim=":", dtype=None, linelen=None, pos=1):
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
            val = line[loc:].strip().split(delim)[pos].split()[0].strip()
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


def keyValuePairTDintoDT(line, key, basedt, delim=":", length=8):
    """
    Given a line and a key supposedly occuring on that line, return its
    value and turn it into a datetime object using another as a starting point.
    This is useful since times are frequently given without an accompanying
    date so we have to be a bit more clever.
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

    # Replace the hours, minutes, seconds of the basedt with those
    #   we read/parse
    dtobj = basedt(hours=np.float(val[0:2]), minutes=np.float(val[3:5]),
                   seconds=np.float(val[7:]))
    return dtobj


def keyValuePairTD(line, key, delim=":", length=8):
    """
    Given a line and a key supposedly occuring on that line, return its
    value and turn it into a timedelta object.  Need a seperate function since
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

    # Can't figure out how to go from a string to a timedelta object so
    #   we're going to go the annoying way around
    dtobj = timedelta(days=0, weeks=0,
                      hours=np.float(val[0:2]), minutes=np.float(val[3:5]),
                      seconds=np.float(val[7:]))
    return dtobj


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
        self.drunway = ''
        self.takeoff = 0
        self.landing = 0
        self.obstime = 0
        self.flighttime = 0
        self.mach = 0
        self.sunset = ''
        self.sunrise = ''
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

    def summarize(self):
        """
        Returns a nice summary string about the current flight
        """
        txtStr = "%s to %s, %d flight legs." %\
                 (self.origin, self.destination, self.nlegs)
        txtStr += "\nTakeoff at %s\nLanding at %s\n" %\
                  (self.takeoff, self.landing)
        txtStr += "Flight duration of %s including %s observing time" %\
                  (str(self.flighttime), self.obstime)

        return txtStr


class legprofile(object):
    """
    Defining several common leg characteristics, to be imbedded inside a
    flightprofile object for easy access.
    """

    def __init__(self):
        self.legno = 0
        self.legtype = ''
        self.target = ''
        self.nonsiderial = False
        self.start = ''
        self.duration = timedelta()
        self.obsdur = timedelta()
        self.altitude = ''
        self.ra = ''
        self.dec = ''
        self.epoch = ''
        self.range_elev = []
        self.range_rof = []
        self.range_rofrt = []
        self.moonangle = 0
        self.utc = []
        self.utcdt = None
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
        self.obsplan = ''

    def summarize(self):
        """
        Returns a nice summary string about the current leg
        """
        txtSummary = ''

        if self.legtype == 'Takeoff':
            txtSummary = "%s %02d" %\
                         (self.legtype, self.legno)
        elif self.legtype == 'Landing':
            txtSummary = "%s %02d" %\
                         (self.legtype, self.legno)
        elif self.legtype == 'Other':
            txtSummary = "%s %02d" %\
                         (self.legtype, self.legno)
        elif self.legtype == 'Observing':
            txtSummary = "%s, RA: %s Dec: %s, Dur: %s ObsDur: %s" %\
                         (self.target, self.ra, self.dec,
                          str(self.duration),
                          str(self.obsdur))
        else:
            pass

        return txtSummary


def regExper(lines, key, keytype='key:val', howmany=1):
    """
    """
    found = 0
    matches = []
    cmatch = None
    mask = ''

    # Leg 4 (HIP 84379)   Start: 04:06:22     Leg Dur: 00:30:00   Req. Alt: 37000 ft
    # ObspID:             Blk:                Priority: C         Obs Dur: 00:00:00
    # Target: HIP 84379   RA: 17h15m01.91s    Dec: 24d50m21.1s    Equinox: J2000.0
    # Elev: [40.9, 34.7]  ROF: [64.9, 59.0] rate: [-0.20, -0.19] deg/min
    # Moon Angle: 50      Moon Illum: 9%      THdg: [4.6, 6.0] rate: [+0.02, +0.06] deg/min
    # https://regex101.com/

    if keytype == 'legtarg':
        mask = u'(%s\s+\d+\s*\(.*\))' % (key)
    elif keytype == 'key:val':
        mask = u'(%s\s*\:\s*\S*)' % (key)
    elif keytype == 'threeline':
        mask = u'((%s\s*\:.*)\s*(%s\s*\:.*)\s*(%s\s*\:.*))' %\
            (key[0], key[1], key[2])
    elif keytype == 'key:dtime':
        mask = u'(%s\s*\:\s*\S*\s*\S*\s*\S*)' % (key)
    elif keytype == 'Vinz':
        print "I am Vinz, Vinz Clortho, Keymaster of Gozer..."
        print "Volguus Zildrohoar, Lord of the Seboullia."
        print "Are you the Gatekeeper?"

    for each in lines:
        if keytype == 'threeline':
            cmatch = re.findall(mask, each.strip())
            if cmatch == []:
                cmatch = None
        else:
            cmatch = re.search(mask, each.strip())

        if cmatch is not None:
            found += 1
            matches.append(cmatch)

    # Some sensible ways to return things to not get overly frustrated later
    if found == 0:
        return None
    elif found == 1:
        return matches[0]
    elif howmany > 1 and found == howmany:
        return matches
    elif found > howmany or found < howmany:
        print "Ambigious search! Asked for %d, but found %d" % (howmany, found)
        print "Returning the first %d..." % (howmany)
        return matches[0:howmany]


def parseLegMetadata(i, words, ltype=None):
    """
    Given a block of lines from the .MIS file that contain the leg's
    metadata and actual data starting lines, parse all the crap in between
    that's important and useful and return the leg class for further use.
    """
    print "Parsing leg %d" % (i)
    newleg = legprofile()
    newleg.legno = i + 1

    # Use the regexp setup used in parseMISPreamble to make this not awful
    legtarg = regExper(words, 'Leg', howmany=1, keytype='legtarg')
    # NOTE: need pos=2 here because it's splitting on the spaces, and the
    #   format is "Leg N (stuff)" and [1:-1] excludes the parentheses
    newleg.target = keyValuePair(legtarg.group(),
                                 "Leg", delim=' ', pos=2, dtype=str)[1:-1]

    start = regExper(words, 'Start', howmany=1, keytype='key:val')
    newleg.start = keyValuePairTD(start.group(), "Start")

    dur = regExper(words, 'Leg Dur', howmany=1, keytype='key:val')
    newleg.duration = keyValuePairTD(dur.group(), "Leg Dur")

    alt = regExper(words, 'Req. Alt', howmany=1, keytype='key:val')
    newleg.altitude = keyValuePair(alt.group(), "Req. Alt", dtype=float)

    # Now we begin the itterative approach to parsing (with some help)
    if ltype == 'Takeoff':
        newleg.target = 'Takeoff'
        newleg.legtype = 'Takeoff'
        return newleg
    elif ltype == 'Landing':
        newleg.target = 'Landing'
        newleg.legtype = 'Landing'
        return newleg
    else:
        # This generally means it's an observing leg
        # If the target keyword is there, it's an observing leg
        print "Lookng for target"
        target = regExper(words, 'Target', howmany=1, keytype='key:val')
        if target is None:
            newleg.legtype = 'Other'
        else:
            newleg.legtype = 'Observing'

            newleg.target = keyValuePair(target.group(), 'Target', dtype=str)
            opidline = regExper(words, ['ObspID', 'Blk', 'Priority'],
                                howmany=1, keytype='threeline')
            opid = opidline
            print newleg.target

#    if newleg.legtype == 'Observing':
#        newleg.obsdur = keyValuePairTD(words[1], "Obs Dur")
#        newleg.ra = keyValuePair(words[2], "RA")
#        newleg.dec = keyValuePair(words[2], "Dec")
#        newleg.epoch = keyValuePair(words[2], "Equinox")
#        newleg.target = keyValuePair(words[2], "Target")
#        newleg.range_elev = keyValuePair(words[3], "Elev")
#        newleg.range_rof = keyValuePair(words[3], "ROF")
#        newleg.range_rofrt = keyValuePair(words[3], "rate")

        return newleg


def parseMISPreamble(lines, flight):
    """
    Returns valuable parameters from the preamble section, such as flight
    duration, locations, etc. directly to the flight class and returns it.

    Does it all with the magic of regular expressions searching across the
    preamble block each time, customizing the searches based on what
    we're actually looking for (keytype).

    """
    # Grab the filename and date of MIS file creation
    filename = regExper(lines, 'Filename', howmany=1, keytype='key:val')
    flight.filename = keyValuePair(filename.group(), "Filename", dtype=str)

    # Note: the saved key is a timestamp, with a space in between stuff.
    saved = regExper(lines, 'Saved', howmany=1, keytype='key:dtime')
    flight.saved = keyValuePairDT(saved.group(), "Saved")

    # Search for two airports; first is takeoff, second is landing
    airports = regExper(lines, 'Airport', howmany=2, keytype='key:val')
    if airports is not None and len(airports) == 2:
        flight.origin = keyValuePair(airports[0].group(),
                                     "Airport", dtype=str)
        flight.destination = keyValuePair(airports[1].group(),
                                          "Airport", dtype=str)
    elif len(airports) != 2 or airports is None:
        print "WARNING: Couldn't find departure/arrival information!"
        flight.origin = "Unknown"
        flight.destination = "Unknown"

    runway = regExper(lines, 'Runway', howmany=1, keytype='key:val')
    flight.drunway = keyValuePair(runway.group(), "Runway", dtype=str)

    legs = regExper(lines, 'Legs', howmany=1, keytype='key:val')
    flight.nlegs = keyValuePair(legs.group(), "Legs", dtype=int)

    mach = regExper(lines, 'Mach', howmany=1, keytype='key:val')
    flight.mach = keyValuePair(mach.group(), "Mach", dtype=float)

    takeoff = regExper(lines, 'Takeoff', howmany=1, keytype='key:dtime')
    flight.takeoff = keyValuePairDT(takeoff.group(), "Takeoff")

    obstime = regExper(lines, 'Obs Time', howmany=1, keytype='key:val')
    flight.obstime = keyValuePairTD(obstime.group(), "Obs Time")

    flttime = regExper(lines, 'Flt Time', howmany=1, keytype='key:val')
    flight.flighttime = keyValuePairTD(flttime.group(), "Flt Time")

    landing = regExper(lines, 'Landing', howmany=1, keytype='key:dtime')
    flight.landing = keyValuePairDT(landing.group(), "Landing")

    sunset = regExper(lines, 'Sunset', howmany=1, keytype='key:val')
    flight.sunset = keyValuePairTD(sunset.group(), "Sunset")

    sunrise = regExper(lines, 'Sunrise', howmany=1, keytype='key:val')
    flight.sunrise = keyValuePairTD(sunrise.group(), "Sunrise")

    print flight.summarize()

    return flight


def parseMIS(infile):
    """
    Read a SOFIA .MIS file, parse it, and return a nice thing we can work with
    """
    # Create an empty base class that we'll fill up as we read through
    flight = flightprofile()

    # Read the file into memory so we can quickly parse stuff
    f = open(infile, 'r')
    cont = f.readlines()
    f.close()

    # Search for the header lines which will tell us how many legs there are.
    #  Use a regular expression to make the searching less awful
    #  Note: regexp searches can be awful no matter what
    head1 = "Leg \d* \(.*\)"
    lhed = findLegHeaders(cont, re.compile(head1))

    # Guarantee that the loop matches the number of legs found
    flight.nlegs = len(lhed)

    head2 = "UTC\s*MHdg"
    ldat = findLegHeaders(cont, re.compile(head2))

    if len(lhed) != len(ldat):
        print "FATAL ERROR: Couldn't find the same amount of legs and data!"
        print "Check the formatting of the file?  Or the regular expressions"
        print "need updating because they changed the file format?"
        print "Looking for '%s' and '%s'" % (head1, head2)
        return -1

    # Since we know where the first leg line is, we can define the preamble.
    #   Takes the flight class as an argument and returns it all filled up.
    flight = parseMISPreamble(cont[0:lhed[0]], flight)

    for i, datastart in enumerate(lhed):
        if i == 0:
            # First leg is always takeoff
            leg = parseLegMetadata(i, cont[lhed[i]:ldat[i]], ltype='Takeoff')
        elif i == (flight.nlegs - 1):
            # Last is always landing
            leg = parseLegMetadata(i, cont[lhed[i]:ldat[i]], ltype='Landing')
        else:
            # Middle legs can be almost anything
            leg = parseLegMetadata(i, cont[lhed[i]:ldat[i]])
        print leg.summarize()


if __name__ == "__main__":
    infile = '/Users/rhamilton/Desktop/HAWCCom2Flights/Draft5/201609_HA_01_SCI.mis'
    parseMIS(infile)
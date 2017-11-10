# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:21:44 2016

@author: rhamilton
"""

# Trying to ensure Python 2/3 coexistance ...
from __future__ import division, print_function

import re
import copy
import hashlib
import itertools
import numpy as np
import scipy.interpolate as spi
from datetime import datetime, timedelta


def sortByDate(inlist):
    """
    Given a random stupid list of flight plans, return the order that
    provides a date-ordered sequence because of course this is something
    that has to be done by hand after the fact
    """

    seq = []
    for i, each in enumerate(inlist):
        # Lightly parse each flight (just reads the preamble)
        #   Putting the last 3 returns of MISlightly into the _ junk var
        flight, _, _, _ = parseMISlightly(each)
        seq.append(flight.takeoff)

    # Sort by takeoff time (flight.takeoff is a datetime obj!)
    newseq = np.argsort(seq)

    return newseq


def go_dt(var):
    return timedelta(seconds=var)


def go_iso(var):
    return var.isoformat()


def commentinator(coms, ctype, btag, tag):
    """
    Given a comment class/structure, append the message 
    to the specified type of comment
    """
    # Construct the message
    tag = btag + tag
    
    if ctype.lower() == 'notes':
        coms.notes.append(tag)
    elif ctype.lower() == 'warning':
        coms.warnings.append(tag)
    elif ctype.lower() == 'error':
        coms.errors.append(tag)
    elif ctype.lower() == 'tip':
        coms.tips.append(tag)
    
    return coms
    

class flightcomments(object):
    """
    Useful for reviewing flight plans and keeping their comments
    """
    def __init__(self):
        self.notes = []
        self.warnings = []
        self.errors = []
        self.tips = []
        self.rating = ''


class seriesreview(object):
    """

    """
    def __init__(self):
        self.seriesname = ''
        self.reviewername = ''
        self.flights = {}
        self.summary = ''
        
    def summarize(self):
        self.progs = {}
        flighthashes = self.flights.keys()
        for fhash in flighthashes:
            flight = self.flights[fhash]
            for eachleg in flight.legs:
                if eachleg.legtype == "Observing":
                    # Group in an obsplan by target name to catch obs
                    #   that are split across multiple flights
                    bundle = {eachleg.target: [[str(flight.takeoff.date()),
                                               str(eachleg.obsdur)]]}
                    # Check to see if the obsplan already has targets in
                    #   the series; if so, append to that so we don't lose any
                    
                    if eachleg.obsplan in self.progs.keys():
#                        print("obsplan %s already here" % (eachleg.obsplan))
                        # Check to see if this target has any other obs
                        targsinprog = self.progs[eachleg.obsplan].keys()
#                        print(targsinprog)

                        # Still need to catch case differences ?
                        if eachleg.target in targsinprog:
#                            print("")
#                            print("another obs of target %s" % eachleg.target)
                            # Need to use atarg here because that was the 
                            #   one already stored and it'll have the correct
                            #   case!
                            sht = self.progs[eachleg.obsplan][eachleg.target]
                            sht.append(bundle[eachleg.target][0])
#                            print("")
                        else:
#                            print("target %s isn't here yet" % (eachleg.target))
                            self.progs[eachleg.obsplan].update(bundle)
                    else:
                        self.progs.update({eachleg.obsplan: bundle})                    
#        print(self.progs)


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
        self.hash = ''
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
        # Fancy name is the new (2016) system for naming flights, like "Ezra"
        self.fancyname = ''
        # Attempted to parse from the filename
        self.instrument = ''
        self.instdict = {"EX": "EXES",
                         "FC": "FLITECAM",
                         "FF": "FPI+",
                         "FI": "FIFI-LS",
                         "FO": "FORCAST",
                         "FP": "FLIPO",
                         "GR": "GREAT",
                         "HA": "HAWC+",
                         "HI": "HIPO",
                         "HM": "HIRMES",
                         "NA": "NotApplicable",
                         "NO": "MassDummy"}
        # In a perfect world, I'd just make this be len(legs)
        self.nlegs = 0
        self.legs = []
        self.reviewComments = flightcomments()

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
        self.range_rofrtu = ''
        self.range_thdg = []
        self.range_thdgrt = []
        self.range_thdgrtu = ''
        self.moonangle = 0
        self.moonillum = ''
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
        self.obsplan = ''
        self.obsblk = ''
        self.nonsid = False
        self.naifid = -1

    def summarize(self):
        """
        Returns a nice summary string about the current leg
        """
        txtSumm = ''

        if self.legtype == 'Takeoff':
            txtSumm = "%02d -- %s" %\
                         (self.legno, self.legtype)
        elif self.legtype == 'Landing':
            txtSumm = "%02d -- %s" %\
                         (self.legno, self.legtype)
        elif self.legtype == 'Other':
            txtSumm = "%02d -- %s" %\
                         (self.legno, self.legtype)
        elif self.legtype == 'Observing':
            txtSumm = "%02d -- %s, RA: %s, Dec: %s, LegDur: %s, ObsDur: %s" %\
                       (self.legno, self.target, self.ra, self.dec,
                        str(self.duration),
                        str(self.obsdur))
            txtSumm += "\n"
            if self.nonsid is True:
                txtSumm += "NONSIDERIAL TARGET -- NAIFID: %d" % (self.naifid)
                txtSumm += "\n"
                txtSumm += "(The SOFIA project sincerely hopes you enjoy "
                txtSumm += "your observing breaks due to XFORMS crashes)"
                txtSumm += "\n"
            txtSumm += "ObsPlan: %s, ObsBlk: %s" % (self.obsplan, self.obsblk)
            txtSumm += "\n\n"
            txtSumm += "Elevation Range: %.1f, %.1f" % (self.range_elev[0],
                                                        self.range_elev[1])
            txtSumm += "\n\n"
            txtSumm += "ROF Range: %.1f, %.1f" % (self.range_rof[0],
                                                  self.range_rof[1])
            txtSumm += "\n"
            txtSumm += "ROF Rate Range: %.1f, %.1f %s" % (self.range_rofrt[0],
                                                          self.range_rofrt[1],
                                                          self.range_rofrtu)
            txtSumm += "\n\n"
            txtSumm += "True Heading Range: %.1f, %.1f" % (self.range_thdg[0],
                                                           self.range_thdg[1])
            txtSumm += "\n"
            txtSumm += "True Heading Rate Range: %.1f, %.1f %s" %\
                (self.range_thdgrt[0],
                 self.range_thdgrt[1],
                 self.range_thdgrtu)
            txtSumm += "\n"
            txtSumm += "Moon Angle: %.1f, Moon Illumination: %s" %\
                (self.moonangle, self.moonillum)

        return txtSumm


def interp_flight(oflight, npts, timestep=55):
    """
    Fill out a leg into a set number of equally spaced points, since the
    .mis file is minimally sparse.

    Interpolate to a baseline of timestep sampling.
    """

    # Let's start with a full copy of the original, and update it as we go
    iflight = copy.deepcopy(oflight)

    rough_delta = iflight.flighttime.seconds/np.float(npts)
    delta = np.around(rough_delta, decimals=0)
    # i == number of legs
    # j == total number of points in flight plan
    i = 0
    j = 0
    for leg in iflight.legs:
        if len(leg.utcdt) > 1:
            # Construct our point timings, done poorly but quickly
            filler = np.arange(leg.relative_time[0],
                               leg.relative_time[-1]+delta,
                               delta)
            # If we popped over, just stop at the leg boundary regardless
            if filler[-1] > leg.relative_time[-1]:
                filler[-1] = leg.relative_time[-1]

            # Check if mhdg or thdg has a zero point crossing that will confuse
            #  the simple minded interpolation that's about to happen

#            print "ORIG THDG:", leg.mhdg
#            print "ORIG MHDG:", leg.thdg
            # This is some pretty dirty logic for right now. Needs cleaning up.
            uprange = False
            for k, hdg in enumerate(leg.mhdg):
                if k != 0:
                    # Check the previous and the current; if it crosses zero,
                    #  then add 360 to keep it monotonicly increasing
                    #  Do this for both magnetic and true headings
                    if leg.mhdg[k-1] >= 350. and leg.mhdg[k] < 10:
                        uprange = True
                    if uprange is True:
                        leg.mhdg[k] += 360.
                    if leg.thdg[k-1] >= 350. and leg.thdg[k] < 10:
                        uprange = True
                    if uprange is True:
                        leg.thdg[k] += 360.
            if uprange is True:
                pass

            # Actually interpolate the points...add more in this style as need
            latprimer = spi.interp1d(leg.relative_time,
                                     leg.lat, kind='linear')
            lonprimer = spi.interp1d(leg.relative_time,
                                     leg.long, kind='linear')
            thdgprimer = spi.interp1d(leg.relative_time,
                                      leg.thdg, kind='linear')
            mhdgprimer = spi.interp1d(leg.relative_time,
                                      leg.mhdg, kind='linear')

            # Replacing the existing stuff with the interpolated values
            leg.lat = latprimer(filler)
            leg.long = lonprimer(filler)
            leg.thdg = thdgprimer(filler) % 360.
            leg.mhdg = mhdgprimer(filler) % 360.

            # Use a stubby little function instead of a loop. Better?
            # Need to explicitly list() map() in Python3 to operate on it
            #   the same way as in Python2
            filler = list(map(go_dt, filler))
            leg.relative_time = filler

            # Recreate timestamps for the new interpolated set, both dt and iso
            #  formatted objects for easy interactions
            leg.utcdt = leg.relative_time + np.repeat(iflight.takeoff,
                                                      len(filler))
            leg.utc = list(map(go_iso, leg.utcdt))

            j += len(leg.long)
            i += 1

#    print "Interpolated %s to roughly fit %d points total," % \
#          (oflight.filename, npts)
#    print "with a delta_t of %06.1f; ended up with %d points total." % \
#          (delta, j)

    return iflight


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
    elif dtype is 'bracketed':
        pass

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


def regExper(lines, key, keytype='key:val', howmany=1, nextkey=None):
    """
    """
    found = 0
    matches = []
    cmatch = None
    mask = ''

    # Oh god I'm sorry it's like it's suddenly all Perl up in here.
    #   Use something like https://regex101.com/ to test against
    if keytype == 'legtarg':
        mask = u'(%s\s+\d+\s*\(.*\))' % (key)
    elif keytype == 'key:val':
        mask = u'(%s\s*\:\s*\S*)' % (key)
    elif keytype == 'key+nextkey':
        mask = u'((%s*\:.*)%s\:)' % (key, nextkey)
    elif keytype == 'threeline':
        mask = u'((%s\s*\:.*)\s*(%s\s*\:.*)\s*(%s\s*\:.*))' %\
            (key[0], key[1], key[2])
    elif keytype == 'bracketvals':
        mask = u'(%s*\:\s*(\[.{0,5}\,\s*.{0,5}\]))' % (key)
    elif keytype == 'bracketvalsunits':
        mask = u'(%s\s*\:\s*(\[.{0,5}\,\s*.{0,5}\])\s*(\w*\/\w*))' % (key)
    elif keytype == 'key:dtime':
        mask = u'(%s\s*\:\s*\S*\s*\S*\s*\S*)' % (key)
    elif keytype == 'Vinz':
        print("I am Vinz, Vinz Clortho, Keymaster of Gozer...")
        print("Volguus Zildrohoar, Lord of the Seboullia.")
        print("Are you the Gatekeeper?")

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
        print("Ambigious search! Asked for %d but found %d" % (howmany, found))
        print("Returning the first %d..." % (howmany))
        return matches[0:howmany]


def isItBlankOrNot(stupidkeyval):
    """
    Blank values are never an acceptable value because then you have to do
    stupid crap like this to parse/work with it later.

    """
    # Annoying magic, but there's no easy way to deal with
    #   completely blank/missing values so we do what we can
    result = stupidkeyval.split(':')
    if len(result) == 1:
        # Can we even get here? Not in any good way
        result = 'Undefined'
    elif len(result) == 2:
        # Expected entry point
        # Check the place where we expect to find the obsplan.
        #   If it's blank, put *something* in it.
        if result[1].strip() == '':
            result = 'Undefined'
        else:
            result = result[1].strip()
    elif result is None:
        result = 'Undefined'

    return result


def parseLegData(i, contents, leg, flight):
    """

    """
#    print "\nParsing leg %d" % (i + 1)
#    print contents
    # I probably should learn to do stuff better than this someday.
    #  Today is not that day, FOR TONIGHT WE DINE IN HELL.
    ptime = 0.
    for j, line in enumerate(contents):
        if line.strip() != '':
            if line.split()[0] == 'UTC':
                start = True
                k = 0
        if start is True:
            line = line.strip().split()
            # If it's a full line (plus maybe a comment)
            if len(line) > 14:
                tobj = datetime.strptime(line[0], "%H:%M:%S")
                # Might contain wrong day, but we'll correct for it
                utcdt = flight.takeoff.replace(hour=tobj.hour,
                                               minute=tobj.minute,
                                               second=tobj.second)
                if k == 0:
                    startdtobj = utcdt
                    leg.elapsedtime.append(0)
                else:
                    # When reconstructing an ISO timestamp, check for a
                    #  change of day that we'll have to set manually
                    if ptime.hour == 23 and utcdt.hour == 0:
                        utcdt.replace(day=flight.takeoff.day + 1)
                        print("Bastard day change")
                    # Start trackin the relative time from start too
                    leg.elapsedtime.append((utcdt-startdtobj).seconds)
                leg.utcdt.append(utcdt)
                leg.relative_time.append((utcdt -
                                          flight.takeoff).seconds)
                leg.utc.append(utcdt.isoformat())

                leg.mhdg.append(np.float(line[1]))
                leg.thdg.append(np.float(line[2]))
#                    leg.lat.append(line[3:5])
                leg.lat.append(np.float(line[3][1:]) +
                               np.float(line[4])/60.)
                if line[3][0] == 'S':
                    leg.lat[-1] *= -1
                leg.long.append(np.float(line[5][1:]) +
                                np.float(line[6])/60.)
                if line[5][0] == 'W':
                    leg.long[-1] *= -1

                leg.wind_dir.append(np.float(line[7].split('/')[0]))
                leg.wind_speed.append(np.float(line[7].split('/')[1]))
                leg.temp.append(np.float(line[8]))
                leg.lst.append(line[9])
                if line[10] == "N/A":
                    leg.elev.append(np.NaN)
                else:
                    leg.elev.append(np.float(line[10]))
                if line[11] == 'N/A':
                    leg.rof.append(np.NaN)
                else:
                    leg.rof.append(np.float(line[11]))
                if line[12] == 'N/A':
                    leg.rofrt.append(np.NaN)
                else:
                    leg.rofrt.append(np.float(line[12]))
                if line[13] == 'N/A':
                    leg.loswv.append(np.NaN)
                else:
                    leg.loswv.append(np.float(line[13]))
                leg.sunelev.append(np.float(line[14]))
                if len(line) == 16:
                    leg.comments.append(line[15])
                else:
                    leg.comments.append('')

                # Store the current datetime for comparison to the next
                ptime = utcdt
                k += 1
        
    return leg


def parseLegMetadata(i, words, ltype=None):
    """
    Given a block of lines from the .MIS file that contain the leg's
    metadata and actual data starting lines, parse all the crap in between
    that's important and useful and return the leg class for further use.
    """
#    print "\nParsing leg %d" % (i + 1)
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
    if alt is None:
        # And it begins; needed for Cycle 5 MIS files due to a name change
        alt = regExper(words, 'Alt.', howmany=1, keytype='key:val')
        newleg.altitude = keyValuePair(alt.group(), "Alt", dtype=float)
    else:
        newleg.altitude = keyValuePair(alt.group(), "Req. Alt", dtype=float)

    # Now we begin the itterative approach to parsing (with some help)
    if ltype == 'Takeoff':
        newleg.target = 'Takeoff'
        newleg.legtype = 'Takeoff'
        newleg.obsblk = 'None'
        return newleg
    elif ltype == 'Landing':
        newleg.target = 'Landing'
        newleg.legtype = 'Landing'
        newleg.obsblk = 'None'
        return newleg
    else:
        # This generally means it's an observing leg
        # If the target keyword is there, it's an observing leg
        target = regExper(words, 'Target', howmany=1, nextkey="RA",
                          keytype='key+nextkey')
        if target is None:
            target = 'Undefined'
            newleg.legtype = 'Other'
        else:
            target = isItBlankOrNot(target.groups()[1])
#            target = target.groups()[1].split(':')[1].strip()
            if target == '':
                target = 'Undefined'
#            newleg.target = target
            # Added this to help with exporting to confluence down the line
            newleg.target = target.replace('[', '').replace(']', '')
            newleg.legtype = 'Observing'

            odur = regExper(words, 'Obs Dur', howmany=1, keytype='key:val')
            newleg.obsdur = keyValuePairTD(odur.group(), "Obs Dur")

            ra = regExper(words, 'RA', howmany=1, keytype='key:val')
            newleg.ra = keyValuePair(ra.group(), "RA", dtype=str)

            epoch = regExper(words, 'Equinox', howmany=1, keytype='key:val')
            newleg.epoch = keyValuePair(epoch.group(), "Equinox", dtype=str)

            dec = regExper(words, 'Dec', howmany=1, keytype='key:val')
            newleg.dec = keyValuePair(dec.group(), "Dec", dtype=str)

            # First shot at parsing blank values. Was a bit hokey.
#            opidline = regExper(words, ['ObspID', 'Blk', 'Priority'],
#                                howmany=1, keytype='threeline')

            opid = regExper(words, 'ObspID', howmany=1, nextkey='Blk',
                            keytype='key+nextkey')
            obsblk = regExper(words, 'Blk', howmany=1, nextkey='Priority',
                              keytype='key+nextkey')

            # Note: these are for the original (threeline) parsing method
#            newleg.obsplan = isItBlankOrNot(opidline[0][1])
#            newleg.obsblk = isItBlankOrNot(opidline[0][2])

            newleg.obsplan = isItBlankOrNot(opid.groups()[1])
            newleg.obsblk = isItBlankOrNot(obsblk.groups()[1])

            naif = regExper(words, 'NAIF ID', howmany=1, keytype='key:val')
            if naif is None:
                newleg.nonsid = False
                newleg.naifid = -1
            else:
                newleg.nonsid = True
                newleg.naifid = keyValuePair(naif.group(), 'NAIF ID',
                                             dtype=int)

            # Big of manual magic to deal with the stupid brackets
            rnge_e = regExper(words, 'Elev', howmany=1, keytype='bracketvals')
            rnge_e = rnge_e.groups()[1][1:-1].split(',')
            newleg.range_elev = [np.float(each) for each in rnge_e]

            rnge_rof = regExper(words, 'ROF', howmany=1, keytype='bracketvals')
            rnge_rof = rnge_rof.groups()[1][1:-1].split(',')
            newleg.range_rof = [np.float(each) for each in rnge_rof]

            # Yet another madman decision - using the same keyword twice!
            #   This will return both the rate for the ROF [0] and the
            #   change in true heading [1]
            # NOTE: Flight plans didn't always have THdg in the metadata,
            #   so if we can't find two, try to just use the one (ROF)
            try:
                rnge_rates = regExper(words, 'rate', howmany=2,
                                      keytype='bracketvalsunits')
                if type(rnge_rates) is not list:
                    # If there's only ROF, it'll find three things and be
                    #   a match re type, not a list of match re types
                    rnge_rofrt = rnge_rates.groups()[1][1:-1].split(',')
                    newleg.range_rofrt = [np.float(ech) for ech in rnge_rofrt]
                    newleg.range_rofrtu = rnge_rates.group()[2]
                else:
                    rnge_rofrt = rnge_rates[0].groups()[1][1:-1].split(',')
                    newleg.range_rofrt = [np.float(ech) for ech in rnge_rofrt]
                    newleg.range_rofrtu = rnge_rates[0].groups()[2]

                    rnge_thdg = regExper(words, 'THdg', howmany=1,
                                         keytype='bracketvals')
                    rnge_thdg = rnge_thdg.groups()[1][1:-1].split(',')
                    newleg.range_thdg = [np.float(each) for each in rnge_thdg]

                    rnge_thdgrt = rnge_rates[1].groups()[1][1:-1].split(',')
                    newleg.range_thdgrt = [np.float(eh) for eh in rnge_thdgrt]
                    newleg.range_thdgrtu = rnge_rates[1].groups()[2]
            except:
                newleg.range_rofrt = "Undefined"
                newleg.range_rofrtu = "Undefined"
                newleg.range_thdgrt = "Undefined"
                newleg.range_thdgrtu = "Undefined"

            moon = regExper(words, 'Moon Angle', howmany=1, keytype='key:val')
            newleg.moonangle = keyValuePair(moon.group(), "Moon", dtype=float)

            # Moon illumination isn't always there
            moonillum = regExper(words, 'Moon Illum',
                                 howmany=1, keytype='key:val')
            if moonillum is not None:
                newleg.moonillum = keyValuePair(moonillum.group(),
                                                "Moon Illum", dtype=str)

        return newleg


def parseMISPreamble(lines, flight, summarize=False):
    """
    Returns valuable parameters from the preamble section, such as flight
    duration, locations, etc. directly to the flight class and returns it.

    Does it all with the magic of regular expressions searching across the
    preamble block each time, customizing the searches based on what
    we're actually looking for (keytype).

    """
    # Attempt to parse stuff from the Flight Plan ID bit. Fancy logic for
    #   grabbing the fancy name, which didn't always exist
    try:
        flightid = regExper(lines, 'Flight Plan ID', howmany=1,
                            keytype='key:val')
        fid = keyValuePair(flightid.group(), "Flight Plan ID", dtype=str)
        fid = fid.strip().split("_")
        if fid[1] != '':
            try:
                flight.instrument = flight.instdict[fid[1].strip()]
            except:
                flight.instrument = ''
        if fid[2] != '':
            flight.fancyname = fid[2]
    except:
        fid = ['', '', '']

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
        print("WARNING: Couldn't find departure/arrival information!")
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

    # NOTE: I hate fp. It sometimes doesn't write sunrise info.
    sunset = regExper(lines, 'Sunset', howmany=1, keytype='key:val')
    try:
        flight.sunset = keyValuePairTD(sunset.group(), "Sunset")
    except:
        flight.sunset = "NONE"

    sunrise = regExper(lines, 'Sunrise', howmany=1, keytype='key:val')
    try:
        flight.sunrise = keyValuePairTD(sunrise.group(), "Sunrise")
    except:
        flight.sunrise = "NONE"

    if summarize is True:
        print(flight.summarize())

    return flight


def parseMISlightly(infile, summarize=False):
    """
    Given a SOFIA .MIS file, just parse the header block and return it
    """
    # Create an empty base class that we'll fill up as we read through
    flight = flightprofile()

    # Read the file into memory so we can quickly parse stuff
    f = open(infile, 'r')
    cont = f.readlines()
    f.close()

    flight.hash = computeHash(infile)

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
        print("FATAL ERROR: Couldn't find the same amount of legs and data!")
        print("Check the formatting of the file?  Or the regular expressions")
        print("need updating because they changed the file format?")
        print("Looking for '%s' and '%s'" % (head1, head2))
        return -1

    # Since we know where the first leg line is, we can define the preamble.
    #   Takes the flight class as an argument and returns it all filled up.
    flight = parseMISPreamble(cont[0:lhed[0]], flight, summarize=summarize)

    return flight, lhed, ldat, cont


def parseMIS(infile, summarize=False):
    """
    Read a SOFIA .MIS file, parse it, and return a nice thing we can work with
    """
    flight, lhed, ldat, cont = parseMISlightly(infile, summarize)

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
#        print leg.summarize()
        if i < len(lhed) - 1:
            leg = parseLegData(i, cont[ldat[i]:lhed[i+1]], leg, flight)
        else:
            leg = parseLegData(i, cont[ldat[i]:], leg, flight)

        flight.legs.append(leg)

    return flight


def computeHash(infile):
    """
    Given an input file, compute and return the sha1() hash of it so
    it can be used as an associative key for other purposes/programs.

    Using sha1() for now because it's trivial.  Anything in hashlib will do!
    """
    f = open(infile, 'rb')
    buffer = f.read()
    f.close()
    return hashlib.sha1(buffer).hexdigest()


if __name__ == "__main__":
    infile = '../../inputs/07_201705_HA_EZRA_WX12.mis'
    flight = parseMIS(infile, summarize=True)
    # In the given flight, go leg by leg and collect the stuff

    seReview = seriesreview()
    seReview.flights.update({flight.hash: flight})
    seReview.summarize()
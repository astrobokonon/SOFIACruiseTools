# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:21:44 2016

@author: rhamilton
"""

# Trying to ensure Python 2/3 coexistence ...
from __future__ import division, print_function

import re
import hashlib
import itertools
import glob
from datetime import datetime, timedelta
import numpy as np
# import copy
# import scipy.interpolate as spi


def sort_by_date(inlist):
    """
    Given a random stupid list of flight plans, return the order that
    provides a date-ordered sequence because of course this is something
    that has to be done by hand after the fact
    """

    seq = []
    for i, each in enumerate(inlist):
        # Lightly parse each flight (just reads the preamble)
        #   Putting the last 3 returns of MISlightly into the _ junk var
        flight_header, _, _, _ = parse_mis_lightly(each)
        seq.append(flight_header.takeoff)

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
    

class FlightComments(object):
    """
    Useful for reviewing flight plans and keeping their comments
    """
    def __init__(self):
        self.notes = []
        self.warnings = []
        self.errors = []
        self.tips = []
        self.rating = ''


class SeriesReview(object):
    """

    """
    def __init__(self):
        self.series_name = ''
        self.reviewer_name = ''
        self.flights = {}
        self.summary = ''
        
    def summarize(self):
        self.progs = {}
        flighthashes = self.flights.keys()
        for fhash in flighthashes:
            flight = self.flights[fhash]
            for eachleg in flight.legs:
                if eachleg.leg_type == "Observing":
                    # Group in an obsplan by target name to catch obs
                    #   that are split across multiple flights
                    try:
                        bundle = {eachleg.astro.target: [[str(flight.takeoff.date()),
                                                   str(eachleg.obs_dur)]]}
                    except:
                        attrs = vars(eachleg)
                        print('\n'.join("%s: %s" % item for item in attrs.items()))

                    # Check to see if the obsplan already has targets in
                    #   the series; if so, append to that so we don't lose any
                    
                    if eachleg.obs_plan in self.progs.keys():
                        # print("obsplan %s already here" % (eachleg.obsplan))
                        # Check to see if this target has any other obs
                        targsinprog = self.progs[eachleg.obs_plan].keys()
                        # print(targsinprog)

                        # Still need to catch case differences ?
                        if eachleg.astro.target in targsinprog:
#                            print("")
#                            print("another obs of target %s" % eachleg.target)
                            # Need to use atarg here because that was the 
                            #   one already stored and it'll have the correct
                            #   case!
                            sht = self.progs[eachleg.obsplan][eachleg.target]
                            sht.append(bundle[eachleg.target][0])
                            # print("")
                        else:
                            # print("target %s isn't here yet" % (eachleg.target))
                            self.progs[eachleg.obs_plan].update(bundle)
                    else:
                        self.progs.update({eachleg.obs_plan: bundle})
        # print(self.progs)


class NonSiderial(object):
    """
    Keeping all the non-siderial object info in a helpful place.
    """
    def __init__(self):
        self.periapse_dist = 0.
        self.ecc = 0.
        self.inclination = 0.
        self.arg_periapse = 0.
        self.long_ascnode = 0.
        self.periapse_jd = 0.
        self.epoch_jd = 0.


class FlightProfile(object):
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
        self.obs_time = 0
        self.flight_time = 0
        self.mach = 0
        self.sunset = ''
        self.sunrise = ''
        # Fancy name is the new (2016) system for naming flights, like "Ezra"
        self.fancy_name = ''
        # Attempted to parse from the filename
        self.instrument = ''
        self.inst_dict = {"EX": "EXES",
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
        self.num_legs = 0
        self.legs = []
        self.review_comments = FlightComments()

    def add_leg(self, parsed_leg):
        self.legs.append(parsed_leg)

    def flat_profile(self, epoch=datetime(1970, 1, 1)):
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
                 (self.origin, self.destination, self.num_legs)
        txtStr += "\nTakeoff at %s\nLanding at %s\n" %\
                  (self.takeoff, self.landing)
        txtStr += "Flight duration of %s including %s observing time" %\
                  (str(self.flight_time), self.obs_time)

        return txtStr


class LegProfile(object):
    """
    Defining several common leg characteristics, to be embedded inside a
    flightprofile object for easy access.
    """

    def __init__(self):
        self.leg_num = 0
        self.leg_type = ''
        self.start = ''
        self.duration = timedelta()
        self.obs_dur = timedelta()
        self.comments = []
        self.obs_plan = ''
        self.obs_blk = ''

        self.astro = AstroProfile()
        self.plane = PlaneProfile()
        self.step = StepParameters()

#        # Astronomy values
#        self.target = ''
#        self.nonsiderial = False
#        self.ra = ''
#        self.dec = ''
#        self.epoch = ''
#        self.moonangle = 0
#        self.moonillum = ''
#        self.nonsid = False
#        self.naifid = -1
#
#        # Plane values
#        self.altitude = ''
#        self.range_elev = []
#        self.range_rof = []
#        self.range_rofrt = []
#        self.range_rofrtu = ''
#        self.range_thdg = []
#        self.range_thdgrt = []
#        self.range_thdgrtu = ''
#
#        # Step values
#        self.utc = []
#        self.utcdt = []
#        self.elapsedtime = []
#        self.mhdg = []
#        self.thdg = []
#        self.lat = []
#        self.long = []
#        self.wind_dir = []
#        self.wind_speed = []
#        self.temp = []
#        self.lst = []
#        self.elev = []
#        self.relative_time = []
#        self.rof = []
#        self.rofrt = []
#        self.loswv = []
#        self.sunelev = []

    def summarize(self):
        """
        Returns a nice summary string about the current leg
        """

        if self.leg_type == 'Observing':
            full_str = ('\n\n{0:02d} -- {1:s}, RA: {2:s}, Dec: {3:s}, '
                        'LegDur: {4:s}, ObsDur: {5:s}\n'.format(self.leg_num,
                                                                self.astro.target,
                                                                self.astro.ra,
                                                                self.astro.dec,
                                                                self.duration,
                                                                self.obs_dur))
            full_str += "\n"
            if self.astro.non_sid:
                sub_str = ('NONSIDERIAL TARGET -- NAIFID: '
                           '{0:d}\n'.format(self.astro.naif_id))
                sub_str += ('(The SOFIA project sincerely hopes you enjoy '
                            'your observing breaks due to XFORMS crashes)\n')
                full_str += sub_str
            full_str += 'ObsPlan: {0:s}, ObsBlk: {1:s}\n\n'.format(self.obs_plan,
                                                                   self.obs_blk)
            print(self.plane.elevation_range)
            try:
                full_str += 'Elevation Range: {0:.1f}, {1:.1f}\n'.format(
                            self.plane.elevation_range[0],
                            self.plane.elevation_range[1])
            except IndexError:
                full_str += 'Elevation Range: None\n'
            try:
                full_str += 'ROF Range: {0:.1f}, {1:.1f}\n'.format(
                            self.plane.rof_range[0],
                            self.plane.rof_range[1])
            except IndexError:
                full_str += 'ROF Range: None\n'
            try:
                full_str += 'ROF Rate Range: {0:.1f}, {1:.1f}\n'.format(
                            self.plane.rof_rate_range[0],
                            self.plane.rof_rate_range[1])
            except (IndexError, ValueError):
                full_str += 'ROF Rate Range: None\n'
            try:
                full_str += 'True Heading Range: {0:.1f}, {1:.1f}\n'.format(
                            self.plane.true_heading_range[0],
                            self.plane.true_heading_range[1])
            except IndexError:
                full_str += 'True Heading Range: None\n'
            try:
                full_str += 'True Heading Rate Range: {0:.1f}, {1:.1f}\n'.format(
                            self.plane.true_heading_rate_range[0],
                            self.plane.true_heading_rate_range[1])
            except (IndexError, ValueError):
                full_str += 'True Heading Rate Range: None\n'
            full_str += 'Moon Angle: {0:.1f}, Moon Illumination: {1:s}'.format(
                        self.astro.moon_angle, self.astro.moon_illum)

#            s = "%02d -- %s, RA: %s, Dec: %s, LegDur: %s, ObsDur: %s" %\
#                       (self.legno, self.target, self.ra, self.dec,
#                        str(self.duration),
#                        str(self.obsdur))
#            s += "ObsPlan: %s, ObsBlk: %s" % (self.obsplan, self.obsblk)
#            s += "\n\n"
#            s += "Elevation Range: %.1f, %.1f" % (self.range_elev[0],
#                                                        self.range_elev[1])
#            s += "\n\n"
#            s += "ROF Range: %.1f, %.1f" % (self.range_rof[0],
#                                                  self.range_rof[1])
#            s += "\n"
#            s += "ROF Rate Range: %.1f, %.1f %s" % (self.range_rofrt[0],
#                                                          self.range_rofrt[1],
#                                                          self.range_rofrtu)
#            s += "\n\n"
#            s += "True Heading Range: %.1f, %.1f" % (self.range_thdg[0],
#                                                           self.range_thdg[1])
#            s += "\n"
#            s += "True Heading Rate Range: %.1f, %.1f %s" %\
#                (self.range_thdgrt[0],
#                 self.range_thdgrt[1],
#                 self.range_thdgrtu)
#            s += "\n"
#            s += "Moon Angle: %.1f, Moon Illumination: %s" %\
#                (self.moonangle, self.moonillum)

        else:
            # Leg is takeoff, landing, or other
            full_str = '{0:02d} -- {1:s}'.format(self.leg_num, self.leg_type)

        return full_str


class AstroProfile(object):
    """
    Class to describe astronomy related parameters
    """
    def __init__(self):
        self.target = ''
        self.nonsiderial = False
        self.ra = ''
        self.dec  = ''
        self.epoch = ''
        self.moon_angle = 0
        self.moon_illum = ''
        self.non_sid = False
        self.naif_id = 0


class PlaneProfile(object):
    """
    Class to describe plane related parameters
    """
    def __init__(self):
        self.altitude = ''
        self.elevation_range = []
        self.rof_range = []
        self.rof_rate_range = []
        self.rof_rate_unit = ''
        self.true_heading_range = []
        self.true_heading_rate_range = []
        self.true_heading_rate_unit = ''


class StepParameters(object):
    """
    Class to describe parameters outlined in 5-minute steps
    """
    def __init__(self):
        self.utc = []
        self.utc_dt = []
        self.elapsed_time = []
        self.magnetic_heading = []
        self.true_heading = []
        self.latitude = []
        self.longitude = []
        self.wind_direction = []
        self.wind_speed = []
        self.temperature = []
        self.local_time = []
        self.elevation = []
        self.relative_time = []
        self.rof = []
        self.rof_rate = []
        self.los_wv = []
        self.sun_elevation = []


# def interp_flight(oflight, npts, timestep=55):
#    """
#    Fill out a leg into a set number of equally spaced points, since the
#    .mis file is minimally sparse.
#
#    Interpolate to a baseline of timestep sampling.
#    """
#
#    # Let's start with a full copy of the original, and update it as we go
#    iflight = copy.deepcopy(oflight)
#
#    rough_delta = iflight.flighttime.seconds/np.float(npts)
#    delta = np.around(rough_delta, decimals=0)
#    # i == number of legs
#    # j == total number of points in flight plan
#    i = 0
#    j = 0
#    for leg in iflight.legs:
#        if len(leg.utcdt) > 1:
#            # Construct our point timings, done poorly but quickly
#            filler = np.arange(leg.relative_time[0],
#                               leg.relative_time[-1]+delta,
#                               delta)
#            # If we popped over, just stop at the leg boundary regardless
#            if filler[-1] > leg.relative_time[-1]:
#                filler[-1] = leg.relative_time[-1]
#
#            # Check if mhdg or thdg has a zero point crossing that will confuse
#            #  the simple minded interpolation that's about to happen
#
##            print "ORIG THDG:", leg.mhdg
##            print "ORIG MHDG:", leg.thdg
#            # This is some pretty dirty logic for right now. Needs cleaning up.
#            uprange = False
#            for k, hdg in enumerate(leg.mhdg):
#                if k != 0:
#                    # Check the previous and the current; if it crosses zero,
#                    #  then add 360 to keep it monotonicly increasing
#                    #  Do this for both magnetic and true headings
#                    if leg.mhdg[k-1] >= 350. and leg.mhdg[k] < 10:
#                        uprange = True
#                    if uprange is True:
#                        leg.mhdg[k] += 360.
#                    if leg.thdg[k-1] >= 350. and leg.thdg[k] < 10:
#                        uprange = True
#                    if uprange is True:
#                        leg.thdg[k] += 360.
#            if uprange is True:
#                pass
#
#            # Actually interpolate the points...add more in this style as need
#            lat_primer = spi.interp1d(leg.relative_time,
#                                     leg.lat, kind='linear')
#            lon_primer = spi.interp1d(leg.relative_time,
#                                     leg.long, kind='linear')
#            thdg_primer = spi.interp1d(leg.relative_time,
#                                      leg.thdg, kind='linear')
#            mhdg_primer = spi.interp1d(leg.relative_time,
#                                      leg.mhdg, kind='linear')
#
#            # Replacing the existing stuff with the interpolated values
#            leg.lat = lat_primer(filler)
#            leg.long = lon_primer(filler)
#            leg.thdg = thdg_primer(filler) % 360.
#            leg.mhdg = mhdg_primer(filler) % 360.
#
#            # Use a stubby little function instead of a loop. Better?
#            # Need to explicitly list() map() in Python3 to operate on it
#            #   the same way as in Python2
#            filler = list(map(go_dt, filler))
#            leg.relative_time = filler
#
#            # Recreate timestamps for the new interpolated set, both dt and iso
#            #  formatted objects for easy interactions
#            leg.utcdt = leg.relative_time + np.repeat(iflight.takeoff,
#                                                      len(filler))
#            leg.utc = list(map(go_iso, leg.utcdt))
#
#            j += len(leg.long)
#            i += 1
#
#    print "Interpolated %s to roughly fit %d points total," % \
#          (oflight.filename, npts)
#    print "with a delta_t of %06.1f; ended up with %d points total." % \
#          (delta, j)
#
#    return iflight


def find_leg_headers(words, header, how='match'):
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


def key_value_pair(line, key, delim=":", dtype=None, linelen=None, pos=1):
    """
    Given a line and a key supposedly occurring on that line, return its
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


def key_value_pair_DT(line, key, delim=":", length=24):
    """
    Given a line and a key supposedly occurring on that line, return its
    value and turn it into a datetime object.  Need a separate function since
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


def key_value_pair_TD(line, key, delim=":", length=8):
    """
    Given a line and a key supposedly occurring on that line, return its
    value and turn it into a timedelta object.  Need a separate function since
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


def reg_exper(lines, key, key_type='key:val', how_many=1, next_key=None):
    """
    """
    found = 0
    matches = []
    cmatch = None
    mask = ''

    # Oh god I'm sorry it's like it's suddenly all Perl up in here.
    #   Use something like https://regex101.com/ to test against
    if key_type == 'legtarg':
        mask = u'(%s\s+\d+\s*\(.*\))' % (key)
    elif key_type == 'key:val':
        mask = u'(%s\s*\:\s*\S*)' % (key)
    elif key_type == 'key+nextkey':
        mask = u'((%s*\:.*)%s\:)' % (key, next_key)
    elif key_type == 'threeline':
        mask = u'((%s\s*\:.*)\s*(%s\s*\:.*)\s*(%s\s*\:.*))' %\
            (key[0], key[1], key[2])
    elif key_type == 'bracketvals':
        mask = u'(%s*\:\s*(\[.{0,5}\,\s*.{0,5}\]))' % (key)
    elif key_type == 'bracketvalsunits':
        mask = u'(%s\s*\:\s*(\[.{0,5}\,\s*.{0,5}\])\s*(\w*\/\w*))' % (key)
    elif key_type == 'key:dtime':
        mask = u'(%s\s*\:\s*\S*\s*\S*\s*\S*)' % (key)
    elif key_type == 'Vinz':
        print("I am Vinz, Vinz Clortho, Keymaster of Gozer...")
        print("Volguus Zildrohoar, Lord of the Seboullia.")
        print("Are you the Gatekeeper?")

    for each in lines:
        if key_type == 'threeline':
            cmatch = re.findall(mask, each.strip())
            if cmatch == []:
                cmatch = None
        else:
            cmatch = re.search(mask, each.strip())

        if cmatch:
            found += 1
            matches.append(cmatch)

    # Some sensible ways to return things to not get overly frustrated later
    if found == 0:
        return None
    elif found == 1:
        return matches[0]
    elif how_many > 1 and found == how_many:
        return matches
    elif found > how_many or found < how_many:
        print("Ambigious search! Asked for {0:d} but found {1:d}".format(how_many,
                                                                         found))
        print("Returning the first {0:d}...".format(how_many))
        return matches[0:how_many]


def is_it_blank_or_not(stupid_keyval):
    """
    Blank values are never an acceptable value because then you have to do
    stupid crap like this to parse/work with it later.
    """
    # Annoying magic, but there's no easy way to deal with
    #   completely blank/missing values so we do what we can
    result = stupid_keyval.split(':')
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


def parse_leg_data(i, contents, leg, flight):
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
                    start_dtobj = utcdt
                    leg.step.elapsed_time.append(0)
                else:
                    # When reconstructing an ISO timestamp, check for a
                    #  change of day that we'll have to set manually
                    if ptime.hour == 23 and utcdt.hour == 0:
                        utcdt.replace(day=flight.takeoff.day + 1)
                        print("Bastard day change")
                    # Start tracking the relative time from start too
                    leg.step.elapsed_time.append((utcdt-start_dtobj).seconds)
                leg.step.utc_dt.append(utcdt)
                leg.step.relative_time.append((utcdt -
                                          flight.takeoff).seconds)
                leg.step.utc.append(utcdt.isoformat())

                leg.step.magnetic_heading.append(np.float(line[1]))
                leg.step.true_heading.append(np.float(line[2]))
#                    leg.lat.append(line[3:5])
                leg.step.latitude.append(np.float(line[3][1:]) +
                               np.float(line[4])/60.)
                if line[3][0] == 'S':
                    leg.step.latitude[-1] *= -1
                leg.step.longitude.append(np.float(line[5][1:]) +
                                np.float(line[6])/60.)
                if line[5][0] == 'W':
                    leg.step.longitude[-1] *= -1

                leg.step.wind_direction.append(np.float(line[7].split('/')[0]))
                leg.step.wind_speed.append(np.float(line[7].split('/')[1]))
                leg.step.temperature.append(np.float(line[8]))
                leg.step.local_time.append(line[9])
                if line[10] == "N/A":
                    leg.step.elevation.append(np.NaN)
                else:
                    leg.step.elevation.append(np.float(line[10]))
                if line[11] == 'N/A':
                    leg.step.rof.append(np.NaN)
                else:
                    leg.step.rof.append(np.float(line[11]))
                if line[12] == 'N/A':
                    leg.step.rof_rate.append(np.NaN)
                else:
                    leg.step.rof_rate.append(np.float(line[12]))
                if line[13] == 'N/A':
                    leg.step.los_wv.append(np.NaN)
                else:
                    leg.step.los_wv.append(np.float(line[13]))
                leg.step.sun_elevation.append(np.float(line[14]))
                if len(line) == 16:
                    leg.comments.append(line[15])
                else:
                    leg.comments.append('')

                # Store the current datetime for comparison to the next
                ptime = utcdt
                k += 1
        
    return leg


def parse_leg_metadata(i, words, ltype=None):
    """
    Given a block of lines from the .MIS file that contain the leg's
    metadata and actual data starting lines, parse all the crap in between
    that's important and useful and return the leg class for further use.
    """
#    print "\nParsing leg %d" % (i + 1)
    new_leg = LegProfile()
    new_leg.leg_num = i + 1

    # Use the regexp setup used in parseMISPreamble to make this not awful
    legtarg = reg_exper(words, 'Leg', how_many=1, key_type='legtarg')
    # NOTE: need pos=2 here because it's splitting on the spaces, and the
    #   format is "Leg N (stuff)" and [1:-1] excludes the parentheses
    new_leg.astro.target = key_value_pair(legtarg.group(),
                                   "Leg", delim=' ', pos=2, dtype=str)[1:-1]

    start = reg_exper(words, 'Start', how_many=1, key_type='key:val')
    new_leg.start = key_value_pair_TD(start.group(), "Start")

    dur = reg_exper(words, 'Leg Dur', how_many=1, key_type='key:val')
    new_leg.duration = key_value_pair_TD(dur.group(), "Leg Dur")

    alt = reg_exper(words, 'Req. Alt', how_many=1, key_type='key:val')
    if alt is None:
        # And it begins; needed for Cycle 5 MIS files due to a name change
        alt = reg_exper(words, 'Alt.', how_many=1, key_type='key:val')
        new_leg.plane.altitude = key_value_pair(alt.group(), "Alt", dtype=float)
    else:
        new_leg.plane.altitude = key_value_pair(alt.group(), "Req. Alt", dtype=float)

    # Now we begin the iterative approach to parsing (with some help)
    if ltype == 'Takeoff':
        new_leg.astro.target = 'Takeoff'
        new_leg.leg_type = 'Takeoff'
        new_leg.obs_blk = 'None'
        return new_leg
    elif ltype == 'Landing':
        new_leg.astro.target = 'Landing'
        new_leg.leg_type = 'Landing'
        new_leg.obs_blk = 'None'
        return new_leg
    else:
        # This generally means it's an observing leg
        # If the target keyword is there, it's an observing leg
        target = reg_exper(words, 'Target', how_many=1, next_key="RA",
                           key_type='key+nextkey')
        if target is None:
            target = 'Undefined'
            new_leg.astro.target = target
            new_leg.leg_type = 'Other'
        else:
            target = is_it_blank_or_not(target.groups()[1])
#            target = target.groups()[1].split(':')[1].strip()
            if target == '':
                target = 'Undefined'
#            newleg.target = target
            # Added this to help with exporting to confluence down the line
            new_leg.astro.target = target.replace('[', '').replace(']', '')
            new_leg.leg_type = 'Observing'

            odur = reg_exper(words, 'Obs Dur', how_many=1, key_type='key:val')
            new_leg.obsdur = key_value_pair_TD(odur.group(), "Obs Dur")

            ra = reg_exper(words, 'RA', how_many=1, key_type='key:val')
            new_leg.ra = key_value_pair(ra.group(), "RA", dtype=str)

            epoch = reg_exper(words, 'Equinox', how_many=1, key_type='key:val')
            new_leg.epoch = key_value_pair(epoch.group(), "Equinox", dtype=str)

            dec = reg_exper(words, 'Dec', how_many=1, key_type='key:val')
            new_leg.dec = key_value_pair(dec.group(), "Dec", dtype=str)

            # First shot at parsing blank values. Was a bit hokey.
#            opidline = regExper(words, ['ObspID', 'Blk', 'Priority'],
#                                howmany=1, keytype='threeline')

            opid = reg_exper(words, 'ObspID', how_many=1, next_key='Blk',
                            key_type='key+nextkey')
            obs_blk = reg_exper(words, 'Blk', how_many=1, next_key='Priority',
                              key_type='key+nextkey')

            # Note: these are for the original (threeline) parsing method
#            newleg.obsplan = isItBlankOrNot(opidline[0][1])
#            newleg.obsblk = isItBlankOrNot(opidline[0][2])

            new_leg.obs_plan = is_it_blank_or_not(opid.groups()[1])
            new_leg.obs_blk = is_it_blank_or_not(obs_blk.groups()[1])

            naif = reg_exper(words, 'NAIF ID', how_many=1, key_type='key:val')
            if naif is None:
                new_leg.non_sid = False
                new_leg.naif_id = -1
            else:
                new_leg.non_sid = True
                new_leg.naif_id = key_value_pair(naif.group(), 'NAIF ID',
                                             dtype=int)

            # Big of manual magic to deal with the stupid brackets
            rnge_e = reg_exper(words, 'Elev', how_many=1, key_type='bracketvals')
            rnge_e = rnge_e.groups()[1][1:-1].split(',')
            new_leg.range_elev = [np.float(each) for each in rnge_e]

            rnge_rof = reg_exper(words, 'ROF', how_many=1, key_type='bracketvals')
            rnge_rof = rnge_rof.groups()[1][1:-1].split(',')
            new_leg.range_rof = [np.float(each) for each in rnge_rof]

            # Yet another madman decision - using the same keyword twice!
            #   This will return both the rate for the ROF [0] and the
            #   change in true heading [1]
            # NOTE: Flight plans didn't always have THdg in the metadata,
            #   so if we can't find two, try to just use the one (ROF)
            try:
                range_rates = reg_exper(words, 'rate', how_many=2,
                                      key_type='bracketvalsunits')
                print('Range_rates = ', [i.group() for i in range_rates])
                #if type(rnge_rates) is not list:
                if isinstance(range_rates, list):
                    # If there's only ROF, it'll find three things and be
                    #   a match re type, not a list of match re types
                    range_rofrt = range_rates.groups()[1][1:-1].split(',')
                    new_leg.plane.rof_rate_range = [np.float(ech) for ech in
                                                    range_rofrt]
                    new_leg.plane.rof_rate_unit = range_rates.group()[2]
                else:
                    range_rofrt = range_rates[0].groups()[1][1:-1].split(',')
                    new_leg.plane.rof_rate_range = [np.float(ech) for ech in
                                                    range_rofrt]
                    new_leg.plane.rof_rate_unit = range_rates[0].groups()[2]

                    range_thdg = reg_exper(words, 'THdg', how_many=1,
                                           key_type='bracketvals')
                    range_thdg = range_thdg.groups()[1][1:-1].split(',')
                    new_leg.plane.true_heading_range = [np.float(each) for each
                                                        in range_thdg]

                    range_thdgrt = range_rates[1].groups()[1][1:-1].split(',')
                    new_leg.plane.true_heading_rate_range = [np.float(eh)
                                                             for eh in range_thdgrt]
                    new_leg.plane.true_heading_rate_unit = range_rates[1].groups()[2]
            except:
                new_leg.plane.rof_rate_range = 'Undefined'
                new_leg.plane.rof_rate_unit = 'Undefined'
                new_leg.plane.true_heading_rate_range = 'Undefined'
                new_leg.plane.true_heading_rate_unit = 'Undefined'

            moon = reg_exper(words, 'Moon Angle', how_many=1, key_type='key:val')
            new_leg.astro.moon_angle = key_value_pair(moon.group(), "Moon",
                                                      dtype=float)

            # Moon illumination isn't always there
            moon_illum = reg_exper(words, 'Moon Illum',
                                 how_many=1, key_type='key:val')
            if moon_illum is not None:
                new_leg.astro.moon_illum = key_value_pair(moon_illum.group(),
                                                          "Moon Illum", dtype=str)

        return new_leg


def parse_mis_preamble(lines, flight, summarize=False):
    """
    Returns valuable parameters from the preamble section, such as flight
    duration, locations, etc. directly to the flight class and returns it.

    Does it all with the magic of regular expressions searching across the
    preamble block each time, customizing the searches based on what
    we're actually looking for (key_type).

    """
    # Attempt to parse stuff from the Flight Plan ID bit. Fancy logic for
    #   grabbing the fancy name, which didn't always exist
    try:
        #flightid = regExper(lines, 'Flight Plan ID', howmany=1,
        flight_id = reg_exper(lines, 'Filename', how_many=1,
                            key_type='key:val')
        #fid = keyValuePair(flightid.group(), "Flight Plan ID", dtype=str)
        fid = key_value_pair(flight_id.group(), "Filename", dtype=str)
        fid = fid.strip().split("_")
        if fid[1] != '':
            try:
                flight.instrument = flight.instdict[fid[1].strip()]
            except IndexError:
                flight.instrument = ''
        if fid[2] != '':
            flight.fancy_name = fid[2]
    except:
        fid = ['', '', '']

    # Grab the filename and date of MIS file creation
    filename = reg_exper(lines, 'Filename', how_many=1, key_type='key:val')
    flight.filename = key_value_pair(filename.group(), "Filename", dtype=str)

    # Note: the saved key is a timestamp, with a space in between stuff.
    saved = reg_exper(lines, 'Saved', how_many=1, key_type='key:dtime')
    flight.saved = key_value_pair_DT(saved.group(), "Saved")

    # Search for two airports; first is takeoff, second is landing
    airports = reg_exper(lines, 'Airport', how_many=2, key_type='key:val')
    if airports and len(airports) == 2:
        flight.origin = key_value_pair(airports[0].group(),
                                     "Airport", dtype=str)
        flight.destination = key_value_pair(airports[1].group(),
                                          "Airport", dtype=str)
    #elif len(airports) != 2 or not airports:
    else:
        print("WARNING: Couldn't find departure/arrival information!")
        flight.origin = "Unknown"
        flight.destination = "Unknown"

    runway = reg_exper(lines, 'Runway', how_many=1, key_type='key:val')
    flight.drunway = key_value_pair(runway.group(), "Runway", dtype=str)

    legs = reg_exper(lines, 'Legs', how_many=1, key_type='key:val')
    flight.num_legs = key_value_pair(legs.group(), "Legs", dtype=int)

    mach = reg_exper(lines, 'Mach', how_many=1, key_type='key:val')
    flight.mach = key_value_pair(mach.group(), "Mach", dtype=float)

    takeoff = reg_exper(lines, 'Takeoff', how_many=1, key_type='key:dtime')
    flight.takeoff = key_value_pair_DT(takeoff.group(), "Takeoff")

    obstime = reg_exper(lines, 'Obs Time', how_many=1, key_type='key:val')
    flight.obs_time = key_value_pair_TD(obstime.group(), "Obs Time")

    flttime = reg_exper(lines, 'Flt Time', how_many=1, key_type='key:val')
    flight.flight_time = key_value_pair_TD(flttime.group(), "Flt Time")

    landing = reg_exper(lines, 'Landing', how_many=1, key_type='key:dtime')
    flight.landing = key_value_pair_DT(landing.group(), "Landing")

    # NOTE: I hate fp. It sometimes doesn't write sunrise info.
    sunset = reg_exper(lines, 'Sunset', how_many=1, key_type='key:val')
    try:
        flight.sunset = key_value_pair_TD(sunset.group(), "Sunset")
    except:
        flight.sunset = "NONE"

    sunrise = reg_exper(lines, 'Sunrise', how_many=1, key_type='key:val')
    try:
        flight.sunrise = key_value_pair_TD(sunrise.group(), "Sunrise")
    except:
        flight.sunrise = "NONE"

    if summarize:
        print(flight.summarize())

    return flight


def parse_mis_lightly(in_file, summarize=False):
    """
    Given a SOFIA .MIS file, just parse the header block and return it
    """
    # Create an empty base class that we'll fill up as we read through
    flight = FlightProfile()

    # Read the file into memory so we can quickly parse stuff
    with open(in_file,'r') as f:
        cont = f.readlines()

    flight.hash = compute_hash(in_file)

    # Search for the header lines which will tell us how many legs there are.
    #  Use a regular expression to make the searching less awful
    #  Note: regexp searches can be awful no matter what
    head1 = "Leg \d* \(.*\)"
    leg_headers = find_leg_headers(cont, re.compile(head1))

    # Guarantee that the loop matches the number of legs found
    flight.num_legs = len(leg_headers)

    head2 = "UTC\s*MHdg"
    leg_data = find_leg_headers(cont, re.compile(head2))

    if len(leg_headers) != len(leg_data):
        print("FATAL ERROR: Couldn't find the same amount of legs and data!")
        print("Check the formatting of the file?  Or the regular expressions")
        print("need updating because they changed the file format?")
        print("Looking for '{0:s}' and '{1:s}'".format(head1, head2))
        return -1

    # Since we know where the first leg line is, we can define the preamble.
    #   Takes the flight class as an argument and returns it all filled up.
    flight = parse_mis_preamble(cont[0:leg_headers[0]], flight,
                                summarize=summarize)

    return flight, leg_headers, leg_data, cont


def parse_mis(in_file, summarize=False):
    """
    Read a SOFIA .MIS file, parse it, and return a nice thing we can work with
    """
    flight, leg_headers, leg_data, cont = parse_mis_lightly(in_file, summarize)

    for i, data_start in enumerate(leg_headers):
        if i == 0:
            # First leg is always takeoff
            leg = parse_leg_metadata(i, cont[leg_headers[i]:leg_data[i]],
                                     ltype='Takeoff')
        elif i == (flight.num_legs - 1):
            # Last is always landing
            leg = parse_leg_metadata(i, cont[leg_headers[i]:leg_data[i]],
                                     ltype='Landing')
        else:
            # Middle legs can be almost anything
            leg = parse_leg_metadata(i, cont[leg_headers[i]:leg_data[i]])
        print(leg.summarize())
        if i < len(leg_headers) - 1:
            leg = parse_leg_data(i, cont[leg_data[i]:leg_headers[i+1]], leg, flight)
        else:
            leg = parse_leg_data(i, cont[leg_data[i]:], leg, flight)

        flight.legs.append(leg)

    return flight


def compute_hash(in_file):
    """
    Given an input file, compute and return the sha1() hash of it so
    it can be used as an associative key for other purposes/programs.

    Using sha1() for now because it's trivial.  Anything in hashlib will do!
    """
    with open(in_file,'rb') as f:
        contents = f.read()
    return hashlib.sha1(contents).hexdigest()


if __name__ == "__main__":
    infile = '../../inputs/07_201705_HA_EZRA_WX12.mis'
    infile = '../../inputs/201710_FP_LINUS_MOPS.mis'
    infile = '../../inputs/201803_FI_DIANA_SCI.mis'
    print('\n', infile.split('/')[-1])
    flight = parse_mis(infile, summarize=True)
    print(flight.instrument)
    # In the given flight, go leg by leg and collect the stuff

    seReview = SeriesReview()
    seReview.flights.update({flight.hash: flight})
    seReview.summarize()

# -*- coding: utf-8 -*-
"""
Created on Fri Aug 30 18:57:54 2013

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
        self.obsplan = ''
        self.nonsiderial = False
        self.start = ''
        self.duration = ''
        self.altitude = ''
        self.ra = ''
        self.dec = ''
        self.epoch = ''
        self.range_elev = ['', '']
        self.range_rof = ['', '']
        self.range_rofrt = ['', '']
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


def mis_str_parse(string):
    """
    Given a header line from a SOFIA .mis file, parse it sensibly and return
    the values of the keywords.

    I should probably rewrite this as part of a comprehensive function that
    gets a leg header and returns a dict, so...TODO that.
    """

    splits = re.split("[^ ]*\:", string)
    return splits


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
#                print "NEW MHDG:", leg.mhdg
#                print "NEW THDG:", leg.thdg
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

            # Use a stubby little lambda function instead of a loop. Better?
            filler = map(go_dt, filler)
            leg.relative_time = filler

            # Recreate timestamps for the new interpolated set, both dt and iso
            #  formatted objects for easy interactions
            leg.utcdt = leg.relative_time + np.repeat(iflight.takeoff,
                                                      len(filler))
            leg.utc = map(go_iso, leg.utcdt)

            j += len(leg.long)
            i += 1

#    print "Interpolated %s to roughly fit %d points total," % \
#          (oflight.filename, npts)
#    print "with a delta_t of %06.1f; ended up with %d points total." % \
#          (delta, j)

    return iflight


def parse_fpmis(infile):
    """
    Try to parse the given file, first in the old style and then if that
    fails then try the new style.

    Hooray.
    """

    try:
        flight = parse_fpmis_old(infile)
    except:
        try:
            flight = parse_fpmis_new(infile)
        except Exception:
            pass

    return flight


def parse_fpmis_new(infile):
    """
    Given a .mis SOFIA flight plan file, parse it sensibly and return
    a class that's easy to interact with to do useful things.

    New style for post Feb. 2015 files.
    """

    # Create an empty base class that we'll fill up as we read through
    flight = flightprofile()

    # Read the file into memory so we can quickly parse stuff
    f = open(infile, 'r')
    contents = np.array(f.readlines())
    f.close()

    flight.filename = contents[0].split()[1]
    flight.saved = ' '.join(contents[0].split()[3:6])

    flight.origin = contents[4].split()[1]
    flight.nlegs = np.int(contents[4].split()[5])

    flight.takeoff = ' '.join(contents[5].split()[1:4])
    # Turn takeoff into a datetime type object
    flight.takeoff = datetime.strptime(flight.takeoff, "%Y-%b-%d %H:%M:%S %Z")
    # datetime ALL THE THINGS
    ts = contents[6].split()[2].split(':')
    flight.obstime = timedelta(days=0, weeks=0,
                               hours=np.float(ts[0]), minutes=np.float(ts[1]),
                               seconds=np.float(ts[2]))
    ts = contents[6].split()[5].split(':')
    flight.flighttime = timedelta(days=0, weeks=0,
                                  hours=np.float(ts[0]),
                                  minutes=np.float(ts[1]),
                                  seconds=np.float(ts[2]))

    # Turn landing into a datetime object too!
    flight.landing = ' '.join(contents[7].split()[1:4])
    flight.landing = datetime.strptime(flight.landing, "%Y-%b-%d %H:%M:%S %Z")
    flight.destination = ' '.join(contents[7].split()[5:])

    # Locate where each leg description begins in the file
    legidx = []
    for i in np.arange(8, len(contents)):
        if contents[i] != '\n' and contents[i].split()[0] == 'Leg':
            legidx.append(i)

    # Make sure we found all the legs that were advertised, or else bail
    if len(contents[legidx]) != flight.nlegs:
        print "FATAL ERROR: %i legs specified, but %i found!" % \
            (flight.nlegs, len(contents[legidx]))
        sys.exit(-1)

    # Now use those locations to parse each leg, adding deets to a class
    #  that gets appended to the main flight class
    i = 0
    for idx in legidx:
        # Set up this new leg class
        leg = legprofile()

        # Check the type of the leg
        if 'Departure' in contents[idx]:
            leg.legtype = 'Departure'
        elif 'Dead' in contents[idx]:
            leg.legtype = 'Dead'
        elif 'Approach' in contents[idx]:
            leg.legtype = 'Approach'
        else:
            leg.legtype = 'Observing'

        # Finish grabbing the leg header information
        leg.start = contents[idx].split('Start:')[1].strip().split()[0]
        leg.duration = contents[idx].split('Dur:')[1].strip().split()[0]
        leg.altitude = contents[idx].split('Alt:')[1].strip().split()[0]
        leg.altitude = np.float(leg.altitude)

        # Note that I'm mostly skipping over the 2nd header line, it wasn't
        #  populated in the sample I was using but it follows similar to above
        if leg.legtype is 'Observing':
            # From header line 2
            leg.obsplan = contents[idx+1].split('ObspID:')[1].strip().split()[0]

            # Leg header row 3
            # Need to be a bit finicky here to account for target names
            partial = contents[idx+2].split('Target:')[1].strip()
            leg.target = partial.split('RA:')[0]
            leg.ra = partial.split('RA:')[1].split()[0]
            leg.dec = partial.split('Dec:')[1].split()[0]
            leg.epoch = partial.split('Equinox:')[1].split()[0]
            # Leg header row 4
            if "orbital" in leg.target:
                leg.nonsiderial = nonsiderial()
                partial = mis_str_parse(contents[idx+3])
                leg.nonsiderial.peridist = np.float(partial[1])
                leg.nonsiderial.ecc = np.float(partial[2])
                leg.nonsiderial.incl = np.float(partial[3])
                leg.nonsiderial.argperi = np.float(partial[4])
                partial = mis_str_parse(contents[idx+4])
                leg.nonsiderial.longascnode = np.float(partial[1])
                leg.nonsiderial.perijd = np.float(partial[2])
                leg.nonsiderial.epochjd = np.float(partial[3])
            else:
                partial = contents[idx+3].split('Elev:')[1]
                range_elev = partial.split('ROF:')[0].strip()
                range_rof = partial.split('ROF:')[1].split('rate:')[0].strip()
                range_rofrt = partial.split('rate:')[1].split('deg')[0].strip()
                leg.moonangle = np.int(partial.split('Angle:')[1].strip())

            # The way I grabbed the ranges sucks, so lets turn the
            #  things into proper arrays for sanity
            leg.range_elev = np.array(range_elev[1:-1].strip().split(','),
                                      dtype=np.float)
            leg.range_rof = np.array(range_rof[1:-1].strip().split(','),
                                     dtype=np.float)
            leg.range_rofrt = np.array(range_rofrt[1:-1].strip().split(','),
                                       dtype=np.float)

        # Parse the rest of this leg, which cosists of N lines of comments
        #  and then a table (with header) followed by any warnings, which
        #  are added to the comments property for completeness.
        if i == len(legidx)-1:
            end = len(contents)
        else:
            end = legidx[i+1]
        # I probably should learn to do stuff better than this someday.
        #  Today is not that day, FOR TONIGHT WE DINE IN HELL.
        start = False
        ptime = 0.
        for j in np.arange(idx+1, end):
            if contents[j].strip() != '':
                if contents[j].split()[0] == 'UTC':
                    start = True
                    k = 0
            if start is True:
                line = contents[j].strip().split()
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
                            print "Bastard day change"
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

        # Final step, increment our ghetto counter
        i += 1
        flight.add_leg(leg)
#    print contents[legidx]
#    print len(contents[legidx])

    return(flight)


def parse_fpmis_old(infile):
    """
    Given a .mis SOFIA flight plan file, parse it sensibly and return
    a class that's easy to interact with to do useful things.

    Old style for .mis files generally before February 2015
    """

    # Create an empty base class that we'll fill up as we read through
    flight = flightprofile()

    # Read the file into memory so we can quickly parse stuff
    f = open(infile, 'r')
    contents = np.array(f.readlines())
    f.close()

    flight.filename = contents[0].split()[1]
    flight.saved = ' '.join(contents[0].split()[3:6])
    flight.origin = contents[5].split()[1]
    flight.nlegs = np.int(contents[5].split()[5])
    flight.takeoff = ' '.join(contents[6].split()[1:4])
    # Turn takeoff into a datetime type object
    flight.takeoff = datetime.strptime(flight.takeoff, "%Y-%b-%d %H:%M:%S %Z")
    # datetime ALL THE THINGS
    ts = contents[7].split()[2].split(':')
    flight.obstime = timedelta(days=0, weeks=0,
                               hours=np.float(ts[0]), minutes=np.float(ts[1]),
                               seconds=np.float(ts[2]))
    ts = contents[7].split()[5].split(':')
    flight.flighttime = timedelta(days=0, weeks=0,
                                  hours=np.float(ts[0]),
                                  minutes=np.float(ts[1]),
                                  seconds=np.float(ts[2]))
    # Turn landing into a datetime object too!
    flight.landing = ' '.join(contents[8].split()[1:4])
    flight.landing = datetime.strptime(flight.landing, "%Y-%b-%d %H:%M:%S %Z")
    flight.destination = ' '.join(contents[8].split()[5:])

    # Locate where each leg description begins in the file
    legidx = []
    for i in np.arange(8, len(contents)):
        if contents[i] != '\n' and contents[i].split()[0] == 'Leg':
            legidx.append(i)

    # Make sure we found all the legs that were advertised, or else bail
    if len(contents[legidx]) != flight.nlegs:
        print "FATAL ERROR: %i legs specified, but %i found!" % \
            (flight.nlegs, len(contents[legidx]))
        sys.exit(-1)

    # Now use those locations to parse each leg, adding deets to a class
    #  that gets appended to the main flight class
    i = 0
    for idx in legidx:
        # Set up this new leg class
        leg = legprofile()

        # Check the type of the leg
        if 'Departure' in contents[idx]:
            leg.legtype = 'Departure'
        elif 'Dead' in contents[idx]:
            leg.legtype = 'Dead'
        elif 'Approach' in contents[idx]:
            leg.legtype = 'Approach'
        else:
            leg.legtype = 'Observing'

        # Finish grabbing the leg header information
        leg.start = contents[idx].split('Start:')[1].strip().split()[0]
        leg.duration = contents[idx].split('Dur:')[1].strip().split()[0]
        leg.altitude = contents[idx].split('Alt:')[1].strip().split()[0]
        leg.altitude = np.float(leg.altitude)

        # Note that I'm skipping over the 2nd header line, it wasn't
        #  populated in the sample I was using but it follows similarly
        if leg.legtype is 'Observing':
            # Leg header row 3
            # Need to be a bit finicky here to account for target names
            partial = contents[idx+2].split('Target:')[1].strip()
            leg.target = partial.split('RA:')[0]
            leg.ra = partial.split('RA:')[1].split()[0]
            leg.dec = partial.split('Dec:')[1].split()[0]
            leg.epoch = partial.split('Equinox:')[1].split()[0]
            # Leg header row 4
            if "orbital" in leg.target:
                leg.nonsiderial = nonsiderial()
                partial = mis_str_parse(contents[idx+3])
                leg.nonsiderial.peridist = np.float(partial[1])
                leg.nonsiderial.ecc = np.float(partial[2])
                leg.nonsiderial.incl = np.float(partial[3])
                leg.nonsiderial.argperi = np.float(partial[4])
                partial = mis_str_parse(contents[idx+4])
                leg.nonsiderial.longascnode = np.float(partial[1])
                leg.nonsiderial.perijd = np.float(partial[2])
                leg.nonsiderial.epochjd = np.float(partial[3])
            else:
                partial = contents[idx+3].split('Elev:')[1]
                range_elev = partial.split('ROF:')[0].strip()
                range_rof = partial.split('ROF:')[1].split('rate:')[0].strip()
                range_rofrt = partial.split('rate:')[1].split('deg')[0].strip()
                leg.moonangle = np.int(partial.split('Angle:')[1].strip())

            # The way I grabbed the ranges sucks, so lets turn the
            #  things into proper arrays for sanity
            leg.range_elev = np.array(range_elev[1:-1].strip().split(','),
                                      dtype=np.float)
            leg.range_rof = np.array(range_rof[1:-1].strip().split(','),
                                     dtype=np.float)
            leg.range_rofrt = np.array(range_rofrt[1:-1].strip().split(','),
                                       dtype=np.float)

        # Parse the rest of this leg, which cosists of N lines of comments
        #  and then a table (with header) followed by any warnings, which
        #  are added to the comments property for completeness.
        if i == len(legidx)-1:
            end = len(contents)
        else:
            end = legidx[i+1]
        # I probably should learn to do stuff better than this someday.
        #  Today is not that day, FOR TONIGHT WE DINE IN HELL.
        start = False
        ptime = 0.
        for j in np.arange(idx+1, end):
            if contents[j].strip() != '':
                if contents[j].split()[0] == 'UTC':
                    start = True
                    k = 0
            if start is True:
                line = contents[j].strip().split()
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
                            print "Bastard day change"
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

        # Final step, increment our ghetto counter
        i += 1
        flight.add_leg(leg)
#    print contents[legidx]
#    print len(contents[legidx])

    return(flight)


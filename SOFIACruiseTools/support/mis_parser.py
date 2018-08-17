# coding: utf-8


from __future__ import print_function
import re
import glob
import hashlib
from datetime import datetime, timedelta
import numpy as np
import itertools


def split_string_size(line, size):
    ''' Splits line into chunks of length size '''
    return [line[i:i + size].strip() for i in range(0, len(line), size)]


class ParseError(Exception):
    """ Generic exception for when parsing fails """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


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
    Hey Hey!
    """

    def __init__(self):
        self.series_name = ''
        self.reviewer_name = ''
        self.flights = {}
        self.summary = ''

    def summarize(self):
        """ Thing """
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

                    # Check to see if the obsplan already has targets in
                    #   the series; if so, append to that so we don't lose any

                    if eachleg.obs_plan in self.progs.keys():
                        # Check to see if this target has any other obs
                        targsinprog = self.progs[eachleg.obs_plan].keys()

                        # Still need to catch case differences ?
                        if eachleg.astro.target in targsinprog:
                            # Need to use atarg here because that was the
                            #   one already stored and it'll have the correct
                            #   case!
                            sht = self.progs[eachleg.obsplan][eachleg.target]
                            sht.append(bundle[eachleg.target][0])
                        else:
                            self.progs[eachleg.obs_plan].update(bundle)
                    else:
                        self.progs.update({eachleg.obs_plan: bundle})


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
        # Typical width of field in each header
        self.size = 20
        self.filename = ''
        self.hash = ''
        self.saved = ''
        self.origin = ''
        self.destination = ''
        self.drunway = ''
        self.takeoff = datetime.utcfromtimestamp(0)
        self.landing = datetime.utcfromtimestamp(0)
        self.obs_time = 0
        self.flight_time = 0
        self.mach = 0
        self.sunset = ''
        self.sunrise = ''
        # Fancy name is the new (2016) system for naming flights, like "Ezra"
        self.fancy_name = ''
        # Attempted to parse from the filename
        self.instrument = ''
        self.inst_dict = {'EX': 'EXES',
                          'FC': 'FLITECAM',
                          'FF': 'FPI+',
                          'FI': 'FIFI-LS',
                          'FO': 'FORCAST',
                          'FP': 'FLIPO',
                          'GR': 'GREAT',
                          'HA': 'HAWC+',
                          'HI': 'HIPO',
                          'HM': 'HIRMES',
                          'NA': 'NotApplicable',
                          'NO': 'MassDummy'}
        # In a perfect world, I'd just make this be len(legs)
        self.num_legs = 0
        self.legs = list()
        self.review_comments = FlightComments()
        self.steps = LegSteps()
        self.leg_steps = list()
        self.step_count = 0

    def __str__(self):
        s = 'Filename: {0:s}\t(Hash: {1:s})\n'.format(self.filename, self.hash)
        s += 'Origin: {0:s}\n'.format(self.origin)
        s += 'Destination: {0:s}\n'.format(self.destination)
        s += 'Destination Runway: {0:s}\n'.format(self.drunway)
        s += 'Takeoff: {0}\n'.format(self.takeoff)
        s += 'Landing: {0}\n'.format(self.landing)
        s += 'Observing Time: {0}\n'.format(self.obs_time)
        s += 'Flight Time: {0}\n'.format(self.flight_time)
        s += 'Mach: {0}\n'.format(self.mach)
        s += 'Sunset: {0}\n'.format(self.sunset)
        s += 'Sunrise: {0}\n'.format(self.sunrise)
        s += 'Instrument: {0}\n'.format(self.instrument)
        s += 'Number of legs: {0:d}\n'.format(len(self.legs))
        return s

    def add_leg(self, parsed_leg):
        """ Doesn't work """
        self.legs.append(parsed_leg)

    def flat_profile(self, epoch=datetime(1970, 1, 1)):
        """ Some Ryan thing"""
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
        s = 'From {0:s} to {1:s}, with {2:d} flight legs\n'.format(self.origin,
                                                                   self.destination,
                                                                   self.num_legs)
        s += 'Takeoff at {0:s}\n'.format(self.takeoff)
        s += 'Landing at {0:s}\n'.format(self.landing)
        s += 'Flight duration of {0:s} including {1:s} observing time\n'.format(
            str(self.flight_time), self.obs_time)
        s += 'Filename: {0:s}'.format(self.filename)

        s += '\n\nMission:\n'
        s += 'Flight Plan ID: {0:s}\n'.format
        s += 'Instrument: {0:s}\n'.format(self.instrument)

        txt_str = "%s to %s, %d flight legs." % (
            self.origin, self.destination, self.num_legs)
        txt_str += "\nTakeoff at %s\nLanding at %s\n" % (self.takeoff, self.landing)
        txt_str += "Flight duration of %s including %s observing time\n" % (
            str(self.flight_time), self.obs_time)
        txt_str += "Filename: %s" % self.filename

        return txt_str

    def parse_mission(self, section, tag):
        """
        Parse the mission section at the top of the flight plan
        """
        lines = section.split('\n')
        if tag == 'Flight':
            # This flight plan has an additional line containing the flight plan id
            # Don't care about this, so pop it off
            lines.pop(0)
        # First line: Airport, Runway, Legs, Mach
        l = lines[0].split()
        self.origin = l[1]
        self.drunway = l[3]
        self.num_legs = int(l[5])
        self.mach = float(l[7])

        # Second line: Takeoff
        takeoff_str = lines[1][9:].strip()
        self.takeoff = datetime.strptime(takeoff_str, '%Y-%b-%d %H:%M:%S %Z')

        # Third line: Observing time, Flight time
        l = lines[2].split()
        observing_str = l[2]
        t_string = datetime.strptime(observing_str, '%H:%M:%S')
        self.obs_time = timedelta(hours=t_string.hour, minutes=t_string.minute,
                                  seconds=t_string.second)
        flight_str = l[5]
        t_string = datetime.strptime(flight_str, '%H:%M:%S')
        self.flight_time = timedelta(hours=t_string.hour,
                                     minutes=t_string.minute,
                                     seconds=t_string.second)

        # Forth line: landing timestamp, landing airport
        l = lines[3].split()
        landing_str = '{0:s} {1:s} {2:s}'.format(l[1], l[2], l[3])
        self.landing = datetime.strptime(landing_str, '%Y-%b-%d %H:%M:%S %Z')
        self.destination = l[5]

        # Fifth line: sunset time, sunset az, sunrise time, sunrise az
        l = lines[4].split()
        self.sunrise = datetime.strptime(l[1], '%H:%M:%S')
        self.sunset = datetime.strptime(l[6], '%H:%M:%S')

    def parse_section(self, section):
        """
        Oversees the parsing of a section of the flight plan

        Identifies the type of leg then calls the correct parser.
        Identification is based on the first word of the section.
        """
        tag = section.split()[0].strip(':')
        if tag == 'Filename':
            filename = section.split()[1]
            instrument_key = filename.split('_')[1]
            self.instrument = self.inst_dict[instrument_key]
            self.filename = filename
        elif tag == 'Flight' or tag == 'Airport':
            # Mission summary
            self.parse_mission(section, tag)
            self.steps.start_date = self.takeoff.date()
        elif tag == 'Leg':
            # This section describes a leg
            # There are different legs:
            #   Takeoff, Landing, Dead, Science, Other
            leg_type = identify_leg_type(section)
            leg = LegProfile()
            if leg_type == 'takeoff':
                leg.parse_takeoff_leg(section, self.size)
            elif leg_type == 'landing':
                leg.parse_landing_leg(section)
            elif leg_type == 'dead':
                leg.parse_dead_leg(section, self.size)
            elif leg_type == 'science':
                leg.parse_science_leg(section, self.size)
            else:
                leg.parse_other_leg(section, self.size)
            self.legs.append(leg)
        elif tag == 'UTC':
            # Section contains 5-minute steps
            self.step_count += 1
            self.steps.parse_steps(section, self.step_count)


class LegSteps(object):
    """Holds details of 5-minute steps of all legs."""
    def __init__(self):
        """Initializes object"""
        self.start_date = None
        self.points = dict()
        keys = ['leg_num', 'time', 'mag_heading', 'true_heading',
                'latitude', 'longitude', 'wind', 'temperature',
                'local_time', 'elevation', 'rof', 'rof_rate',
                'loswv', 'sun_elevation', 'sun_hour_angle']
        for key in keys:
            self.points[key] = list()

#        self.leg_num = list()
#        self.time = list()
#        self.mag_heading = list()
#        self.true_heading = list()
#        self.latitude = list()
#        self.longitude = list()
#        self.wind = list()
#        self.temperature = list()
#        self.local_time = list()
#        self.elevation = list()
#        self.rof = list()
#        self.rof_rate = list()
#        self.loswv = list()
#        self.sun_elevation = list()
#        self.sun_hour_angle = list()

    def parse_steps(self, section, leg_num):
        """Parses 5-minute steps in a leg

        Parameters
        ----------
        section : basestring
            Contains the section details
        leg_num : int
            The number this leg is in the flight

        Returns
        -------
        None
        """

        lines = section.strip().split('\n')
        header = lines[0]
        # The fields present in the steps have changed over time. At some
        # point they added a sun hour angle field. Check if it is present.
        # If it isn't, then it is an old flight plan and don't try to add
        # the hour angle field
        if 'SunHA' in header:
            new_style = True
        else:
            new_style = False
        steps = lines[1:]
        for line in steps:
            if 'Potential' in line:
                break
            self.points['leg_num'].append(leg_num)
            l = line.strip().split()

            utc_time = datetime.strptime(l[0], '%H:%M:%S')
            utc_time = utc_time.replace(year=self.start_date.year,
                                        month=self.start_date.month,
                                        day=self.start_date.day)
            if self.points['time']:
                if utc_time < self.points['time'][-1]:
                    utc_time += datetime.timedelta(days=1)
            self.points['time'].append(utc_time)


            self.points['mag_heading'].append(float(l[1]))
            self.points['true_heading'].append(float(l[2]))
            self.points['latitude'].append(lat_long_convert(l[3]+' '+l[4]))
            self.points['longitude'].append(lat_long_convert(l[5]+' '+l[6]))
            self.points['wind'].append(l[7])
            self.points['temperature'].append(float(l[8]))
            self.points['local_time'].append(l[9])

            try:
                value = float(l[10])
            except ValueError:
                value = np.nan
            finally:
                self.points['elevation'].append(value)

            try:
                value = float(l[11])
            except ValueError:
                value = np.nan
            finally:
                self.points['rof'].append(value)

            try:
                value = float(l[12])
            except ValueError:
                value = np.nan
            finally:
                self.points['rof_rate'].append(value)

            try:
                value = float(l[13])
            except ValueError:
                value = np.nan
            finally:
                self.points['loswv'].append(value)

            self.points['sun_elevation'].append(float(l[14]))
            if new_style:
                self.points['sun_hour_angle'].append(value)


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
        self.priority = ''
        self.rof_rate_range = ''
        self.rof_range = ''
        self.rof_rate_unit = ''

        self.astro = AstroProfile()
        self.plane = PlaneProfile()
        self.step = StepParameters()

    def __str__(self):
        s = '\nLeg: {0:d} ({1:s})\n'.format(self.leg_num, self.leg_type)
        s += 'Start: {0}\n'.format(self.start)
        s += 'Duration: {0} total, {1} observing\n'.format(self.duration,
                                                           self.obs_dur)
        s += 'Obs_plan: {0:s}\n'.format(self.obs_plan)
        s += 'Obs_blk: {0:s}\n'.format(self.obs_blk)
        if self.leg_type == 'science':
            s += str(self.astro)
            s += str(self.plane)
        return s

    def parse_science_leg(self, section, size):
        """ Parses a science leg, filling LegProfile leg """
        lines = section.split('\n')
        # Remove possible nonsense lines that start with blank space
        lines = [l for l in lines if len(l)-len(l.lstrip()) == 0]
        # size = 20

        # Line 1: Leg number, start time, duration, altitude
        # Formatted to fields 20 characters wide
        parsed = self.parse_first_line(lines[0])
        # parsed = leg_num, description, start, duration, altitude
        self.leg_num = parsed[0]
        self.leg_type = 'science'
        self.start = parsed[2]
        self.duration = parsed[3]
        self.plane.altitude = parsed[4]

        # Line 2: ObspID, Blk, Priority, Obs Duration
        line = lines[1].strip()
        l = split_string_size(line, size)
        # l = [line[i:i + size].strip() for i in range(0, len(line), size)]
        # ObspID
        self.obs_plan = l[0].split(':')[1].strip()
        # Obs blk
        self.obs_blk = l[1].split(':')[1].strip()
        # Priority
        self.priority = l[2].split(':')[1].strip()
        # Observation duration
        t_string = datetime.strptime(l[3].split()[-1], '%H:%M:%S')
        self.obs_dur = timedelta(hours=t_string.hour, minutes=t_string.minute,
                                 seconds=t_string.second)

        # Line 3: Target, RA, DEC, Equinox
        line = lines[2].strip()
        l = split_string_size(line, size)
        # Target
        self.astro.target = l[0].split(':')[-1].strip()
        # RA
        self.astro.ra = l[1].split(':')[-1].strip()
        # Dec
        self.astro.dec = l[2].split(':')[-1].strip()
        # Equinox
        self.astro.epoch = l[3].split(':')[-1].strip()

        # Line 4a: Careful, there are multiple versions
        # If object is non-siderial, this line just as naif_id.
        # If the object is siderial, this line is missing
        if 'NAIF ID' in lines[3]:
            line = lines.pop(3)
            self.astro.naif_id = int(line.split(':')[1])
            self.astro.nonsiderial = True
            self.astro.non_sid = True

        # Line 4:
        # Where things get hard, since the fields are not longer
        # 20 characters long. To compound it, there are two different
        # formats for this line, depending on when the flight plan was made.
        # From what I can tell, the different styles can be identified by if
        # the FPI keyword is present. This also determines if there is a fifth line
        # if 'FPI' in lines[3]
        if len(lines) > 4:
            line = lines[3].strip()
            # Line 4: Elevation range, ROF range, ROF rate range, ROF rate unit, FPI
            # Ranges are contained in square backets
            pattern = re.compile(r'\[(.*?)\]')
            l = re.findall(pattern, line)
            # First field: elevation range:
            self.plane.elevation_range = [float(i) for i in l[0].split(',')]
            # Second field: ROF range:
            self.plane.rof_range = [float(i) for i in l[1].split(',')]
            # Third field: ROF rate range:
            self.plane.rof_rate_range = [float(i) for i in l[2].split(',')]
            # ROF rate unit:
            self.plane.rof_rate_unit = line.split(':')[3].split()[2].strip()
            if 'FPI' in line:
                # FPI is the last field:
                self.plane.fpi = int(line.split(':')[-1])

            # Line 5: Moon angle, Moon illumination, True heading range,
            # True heading rate range, True heading rate unit
            line = lines[4].strip()
            # Moon angle:
            self.astro.moon_angle = int(line.split(':')[1].split()[0])
            # Moon illumination
            self.astro.moon_illum = line.split(':')[2].split()[0]
            # True heading range
            # This and true heading rate range use the same bracket notation as
            # ROF rate and ROF rate range
            l = re.findall(pattern, line)
            # True heading range
            self.plane.true_heading_range = [float(i) for i in l[0].split(',')]
            # True heading rate range
            self.plane.true_heading_rate_range = [float(i) for i in l[1].split(',')]
            # True heading rate unit
            self.plane.true_heading_rate_unit = line.split()[-1]

        else:
            # Old format
            # Line 4: Elevation range, ROF range, ROF rate range,
            # ROF range unit, Moon angle
            line = lines[3].strip()
            # Use the same bracket searching for the ranges
            pattern = re.compile(r'\[(.*?)\]')
            l = re.findall(pattern, line)
            # First field: Elevation range
            self.plane.elevation_range = [float(i) for i in l[0].split(',')]
            # Second field: ROF range
            self.rof_range = [float(i) for i in l[1].split(',')]
            # Third field: ROF rate range
            self.rof_rate_range = [float(i) for i in l[2].split(',')]
            # No more brackets
            # ROF rate unit:
            self.rof_rate_unit = line.split()[-4]
            # Last field: Moon angle
            #try:
            self.astro.moon_angle = int(line.split()[-1])
            # No line 5 for the old format

    def parse_takeoff_leg(self, section, size):
        """
        Parts the takeoff/departure leg, filling a LegProfile object
        """
        lines = section.split('\n')
        # Line 1: Leg description, start time, duration, altitude
        parsed = self.parse_first_line(lines[0])
        # parsed = leg_num, description, start, duration, altitude
        self.leg_num = parsed[0]
        self.leg_type = parsed[1]
        self.start = parsed[2]
        self.duration = parsed[3]
        self.plane.altitude = parsed[4]

        # Line 2: Runway, End Latitude, End Longitude, Sunset, Sunset Az
        # Ignore Sunset and Sunset Az as they are contained in the mission section
        line = lines[1].strip()
        l = split_string_size(line, size)
        # Runway
        self.plane.takeoff_runway = l[0].split()[-1]
        # Ending latitude
        self.plane.takeoff_latitude = l[1].split(':')[-1].strip()
        # Ending longitude
        self.plane.takeoff_longitude = l[2].split(':')[-1].strip()

    def parse_landing_leg(self, section):
        """
        Parse the landing leg

        This is a bit different as the fields don't have fixed size.
        Luckily only the first line is of interested. The rest of the
        section had information that's repeated from the mission section.
        """
        lines = section.split('\n')
        # First line: leg info, start, duration, altitude
        l = lines[0]
        self.leg_num = int(l.split()[1])
        self.leg_type = 'landing'
        # Start time
        start_string = l.split('Start:')[-1].split()[0]
        t_string = datetime.strptime(start_string, '%H:%M:%S')
        self.start = timedelta(hours=t_string.hour, minutes=t_string.minute,
                               seconds=t_string.second)
        # Duration
        duration_string = l.split('Dur:')[-1].split()[0]
        t_string = datetime.strptime(duration_string, '%H:%M:%S')
        self.duration = timedelta(hours=t_string.hour, minutes=t_string.minute,
                                  seconds=t_string.second)
        # Altitude
        self.plane.altitude = l.split(':')[1].split()[0].strip()

    def parse_other_leg(self, section, size):
        """
        Parses generic leg

        Due to the various "random" legs, only pull off the
        first line, containing leg number, description, start
        time, duration, and altitude
        """
        lines = section.split('\n')
        parsed = self.parse_first_line(lines[0])
        # parsed = leg_num, description, start, duration, altitude
        self.leg_num = parsed[0]
        self.leg_type = parsed[1]
        self.start = parsed[2]
        self.duration = parsed[3]
        self.plane.altitude = parsed[4]

        self.leg_num, self.start, self

    def parse_dead_leg(self, section, size):
        """
        Parses a dead leg

        Just get the times, nothing else is needed.
        """
        lines = section.split('\n')
        parsed = self.parse_first_line(lines[0])
        # parsed = leg_num, description, start, duration, altitude
        self.leg_num = parsed[0]
        self.leg_type = 'Dead'
        self.start = parsed[2]
        self.duration = parsed[3]
        self.plane.altitude = parsed[4]

    def parse_first_line(self, line):
        """
        Parses the first line of a section.

        The first line is the one most likely to have problems,
        hence why it is in a separate method. The problem occurs when
        the description is too long, pushing it into the next field.
        This breaks the "20-character wide" formatting used everywhere else
        :param line:
        :return:
        """
        # l = split_string_size(line, size)
        # l = [line[i:i+size].strip() for i in range(0,len(line),size)]
        # leg_num = int(l[0].split()[1])

        l = line.split()
        leg_num = int(l[1])
        start_ind = l.index('Start:')
        dur_ind = l.index('Dur:')
        description = ' '.join(l[2:start_ind])[1:-1].lower()
        # Start time
        t_string = datetime.strptime(l[start_ind+1].split()[-1], '%H:%M:%S')
        start = timedelta(hours=t_string.hour, minutes=t_string.minute,
                          seconds=t_string.second)
        # Duration
        t_string = datetime.strptime(l[dur_ind+1].split()[-1], '%H:%M:%S')
        duration = timedelta(hours=t_string.hour, minutes=t_string.minute,
                             seconds=t_string.second)
        # Altitude
        if l[-1] == 'ft':
            altitude = l[-2]
        else:
            altitude = l[-1]
        return leg_num, description, start, duration, altitude

    def test_parse(self):
        """
        Verifies that the leg has been successfully parsed

        Conditions:
        All legs have a start and duration time
        All legs have a type
        All legs have altitude
        All science legs have a target
        All legs have a leg number

        Verify all conditions with assert
        """
        assert self.leg_num != 0
        assert self.leg_type
        if self.leg_type != 'departure':
            assert self.start, 'Type = {0}'.format(self.leg_type)
        assert self.duration
        if self.leg_type == 'science':
            assert self.astro.target
            assert self.astro.ra
            assert self.astro.dec


class AstroProfile(object):
    """
    Class to describe astronomy related parameters
    """

    def __init__(self):
        self.target = ''
        self.nonsiderial = False
        self.ra = ''
        self.dec = ''
        self.epoch = ''
        self.moon_angle = 0
        self.moon_illum = ''
        self.non_sid = False
        self.naif_id = 0

    def __str__(self):
        s = '\nTarget = {0:s}\n'.format(self.target)
        if self.nonsiderial:
            s += '\tNon-Siderial\t'
            s += '\tNAIF_ID: {0:d}\n'.format(self.naif_id)
        else:
            s += '\tSiderial\n'
        s += '\tRA: {0:s}\tDEC: {1:s}\t ({2:s})\n'.format(self.ra, self.dec,
                                                          self.epoch)
        s += '\tMoon: {0:d}\t{1:s}\n'.format(self.moon_angle, self.moon_illum)
        return s


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
        self.takeoff_runway = ''
        self.takeoff_latitude = ''
        self.takeoff_longitude = ''
        self.fpi = ''

    def __str__(self):
        s = '\nPlane:\n'
        s += '\tTakeoff: {0:s}, {1:s}, Runway {2:s}\n'.format(self.takeoff_latitude,
                                                              self.takeoff_longitude,
                                                              self.takeoff_runway)
        s += '\tAltitude: {0:s}'.format(self.altitude)
        try:
            s += '\tElevation: {0} - {1} ft.\n'.format(self.elevation_range[0],
                                                       self.elevation_range[1])
        except IndexError:
            s += '\tElevation Range: {0}\n'.format(self.elevation_range)
        s += '\tRate of Field:\n'
        try:
            s += '\t\tRange: {0} - {1}\n'.format(self.rof_range[0],
                                                 self.rof_range[1])
        except IndexError:
            s += '\t\tRange: {0:s}\n'.format(self.rof_range)
        try:
            s += '\t\tRate Range: {0} - {1}  {2:s}\n'.format(self.rof_rate_range[0],
                                                             self.rof_rate_range[1],
                                                             self.rof_rate_unit)
        except IndexError:
            s += '\t\tRate Range: {0} {1:s}\n'.format(self.rof_rate_range,
                                                      self.rof_rate_unit)
        s += '\tTrue Heading:\n'
        try:
            s += '\t\tRange: {0} - {1}\n'.format(self.true_heading_range[0],
                                                 self.true_heading_range[1])
        except IndexError:
            s += '\t\tRange: {0}\n'.format(self.true_heading_range)
        try:
            s += '\t\tRate Range: {0} - {1}  {2:s}\n'.format(
                self.true_heading_rate_range[0], self.true_heading_rate_range[1],
                self.true_heading_rate_unit)
        except IndexError:
            s += '\t\tRate Range: {0} {1:s}\n'.format(self.true_heading_rate_range,
                                                      self.true_heading_rate_unit)
        return s


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


def lat_long_convert(coord):
    """ Converts 'DD MM' to decimal

    Parameters
    ----------
    coord : str
        Coordinates to convert in a format like 'N37 30'

    Returns
    -------
    point : float
        Coordinates in a format like '37.5'

    Examples
    --------
    >>> lat_long_convert('S43 36.3')
    -43.605

    >>>> lat_long_convert('E172 31.8')
    172.53

    """
    direction = coord[0]
    degrees = float(coord[1:].split()[0])
    minutes = float(coord[1:].split()[1])
    point = degrees + minutes/60.
    if direction in ['W', 'S']:
        point *= -1
    return point


def identify_leg_type(section):
    """
    Identifies the leg type.
    Returns the leg type: 'science','takeoff','landing','dead','other'
    """
    lines = section.split('\n')
    # Get the leg number
    try:
        leg_num = int(lines[0].split()[1])
    except IndexError:
        print('Cannot parse leg_num from: ')
        print(lines[0])
        raise ParseError(lines[0])
    else:
        description = lines[0][lines[0].find('('):lines[0].find(')') + 1]
        if leg_num == 1:
            # First leg is always takeoff
            leg_type = 'takeoff'
        elif 'approach' in description.lower():
            # Landing leg
            leg_type = 'landing'
        elif 'dead' in description.lower():
            # One way to identify a dead leg
            leg_type = 'dead'
        elif lines[1].startswith('ObspID'):
            # As far as I can tell, only science legs have the ObspID field
            leg_type = 'science'
        else:
            leg_type = 'other'
    return leg_type


def summary_object(flight_obj):
    """ Very generic summary of object attributes. """
    attrs = vars(flight_obj)
    s = []
    for item in attrs.items():
        s.append('{0}: {1}'.format(item[0], item[1]))
    return '\n'.join(s)


def parse_mis_file(filename):
    """
    Main control

    Open the MIS file given by filename, 
    returns a filled out FlightProfile
    """
    flight = FlightProfile()
    with open(filename, 'r') as f:
        data = f.read()
    flight.hash = hashlib.sha1(data.encode('utf-8')).hexdigest()
    sections = re.split(r'\n{2}', data)
    for section in sections:
        flight.parse_section(section.strip())
    return flight


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    #loc = '/home/jrvander/code/SOFIACruiseTools/inputs/'
    loc = '/home/jrvander/'
    filenames = glob.glob(loc + '*mis')
    tags = ['Filename:', 'Flight', 'Leg', 'UTC', 'Comment:',
            '============================= ', 'Airport:']
    for fname in filenames:
        fname = loc + '201807_HA_IAGO_MOPS.mis'

        print('\n', fname.split('/')[-1])
        flight = FlightProfile()
        with open(fname, 'r') as f:
            data = f.read()
        flight.hash = hashlib.sha1(data.encode('utf-8')).hexdigest()
        sections = re.split(r'\n{2}', data)
        for section in sections:
            flight.parse_section(section.strip())

        print(flight)
        for i, l in enumerate(flight.legs):
            print(l)
            l.test_parse()

        print('Number of legs: ',flight.num_legs)
        print('Number of details found: ',len(flight.leg_steps))
        print('Unique leg numbers: ',set(flight.steps.points['leg_num']))

        fig,ax = plt.subplots(1,1,figsize=(10,10))
        ax.plot(flight.steps.points['time'])
        fig.savefig('time_points.png',bbox_inches='tight')
        plt.close(fig)

        break

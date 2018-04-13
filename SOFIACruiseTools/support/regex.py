# coding: utf-8


from __future__ import print_function
import re
import glob
import hashlib
from datetime import datetime, timedelta
import itertools


def split_string_size(line, size):
    ''' Splits line into chunks of length size '''
    return [line[i:i + size].strip() for i in range(0, len(line), size)]


class ParseError(Exception):
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

        txtStr = "%s to %s, %d flight legs." % (
        self.origin, self.destination, self.num_legs)
        txtStr += "\nTakeoff at %s\nLanding at %s\n" % (self.takeoff, self.landing)
        txtStr += "Flight duration of %s including %s observing time\n" % (
        str(self.flight_time), self.obs_time)
        txtStr += "Filename: %s" % self.filename

        return txtStr

    def parse_mission(self, section, tag):
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
        t = datetime.strptime(observing_str, '%H:%M:%S')
        self.obs_time = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        flight_str = l[5]
        t = datetime.strptime(flight_str, '%H:%M:%S')
        self.flight_time = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

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
        tag = section.split()[0]
        if tag == 'Filename:':
            filename = section.split()[1]
            instrument_key = filename.split('_')[1]
            self.instrument = self.inst_dict[instrument_key]
            self.filename = filename
        elif tag == 'Flight' or tag == 'Airport':
            # Mission summary
            self.parse_mission(section, tag)
        elif tag == 'Leg':
            # This section describes a leg
            # There are different legs:
            #   Takeoff, Landing, Dead, Science, Other
            leg_type = identify_leg_type(section)
            leg = LegProfile()
            if leg_type == 'takeoff':
                leg.parse_takeoff_leg(section, self.size)
            elif leg_type == 'landing':
                leg.parse_landing_leg(section, self.size)
            elif leg_type == 'dead':
                leg.parse_dead_leg(section, self.size)
            elif leg_type == 'science':
                leg.parse_science_leg(section, self.size)
            else:
                leg.parse_other_leg(section, self.size)
            self.legs.append(leg)


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
        if self.leg_type=='science':
            s += str(self.astro)
            s += str(self.plane)
        return s

    def parse_science_leg(self, section, size):
        """ Parses a science leg, filling LegProfile leg """
        lines = section.split('\n')
        # size = 20

        # Line 1: Leg number, start time, duration, altitude
        # Formatted to fields 20 characters wide
        line = lines[0].strip()
        l = split_string_size(line, size)
        # l = [line[i:i+size].strip() for i in range(0,len(line),size)]
        self.leg_num = int(l[0].split()[1])
        self.leg_type = 'science'
        # Start time
        t = datetime.strptime(l[1].split()[-1], '%H:%M:%S')
        self.start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Duration
        t = datetime.strptime(l[2].split()[-1], '%H:%M:%S')
        self.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Altitude
        self.plane.altitude = l[3].split(':')[-1].split()[0].strip()

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
        t = datetime.strptime(l[3].split()[-1], '%H:%M:%S')
        self.obs_dur = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

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
        if 'FPI' in lines[3]:
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
            self.astro.moon_angle = int(line.split()[-1])

            # No line 5 for the old format

    def parse_takeoff_leg(self, section, size):
        """
        Parts the takeoff/departure leg, filling a LegProfile object
        """
        lines = section.split('\n')
        # Line 1: Leg description, start time, duration, altitude
        line = lines[0].strip()
        l = split_string_size(line, size)
        # Let number and type
        self.leg_num = int(l[0].split()[1])
        self.leg_type = 'takeoff'
        # Start time
        t = datetime.strptime(l[1].split()[-1], '%H:%M:%S')
        self.start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Duration
        t = datetime.strptime(l[2].split()[-1], '%H:%M:%S')
        self.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Altitude
        self.plane.altitude = l[3].split(':')[1].split()[0].strip()

        # Line 2: Runway, End Latitude, End Longitude, Sunset, Sunset Az
        # Ignore Sunset and Sunset Az as they are contained in the mission section
        line = lines[1].strip()
        l = split_string_size(line, size)
        # Runway
        self.plane.takeoff_runway = int(l[0].split()[-1])
        # Ending latitude
        self.plane.takeoff_latitude = l[1].split(':')[-1].strip()
        # Ending longitude
        self.plane.takeoff_longitude = l[2].split(':')[-1].strip()

    def parse_landing_leg(self, section, size):
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
        t = datetime.strptime(start_string, '%H:%M:%S')
        self.start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Duration
        duration_string = l.split('Dur:')[-1].split()[0]
        t = datetime.strptime(duration_string, '%H:%M:%S')
        self.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
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
        parsed = self.parse_first_line(lines[0], size)
        self.leg_num, self.start, self

        self.leg_num = int(l[0].split()[1])
        self.leg_type = l[0].split()[-1].strip('()')
        # Start time
        t = datetime.strptime(l[1].split()[-1], '%H:%M:%S')
        self.start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Duration
        t = datetime.strptime(l[2].split()[-1], '%H:%M:%S')
        self.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        # Altitude
        self.plane.altitude = l[3].split(':')[1].split()[0].strip()

    def parse_first_line(self, line, size):
        """
        Parses the first line of a section.

        The first line is the one most likely to have problems,
        hence why it is in a separate method. The problem occurs when
        the description is too long, pushing it into the next field.
        This breaks the "20-character wide" formatting used everywhere else
        :param line:
        :return:
        """
        l = split_string_size(line, size)
        # l = [line[i:i+size].strip() for i in range(0,len(line),size)]
        leg_num = int(l[0].split()[1])
        description = line.split()[2][1:-1]
        # Start time
        try:
            t = datetime.strptime(l[1].split()[-1], '%H:%M:%S')
        except ValueError:
            start_string = line.split('Start:')[-1].split()[0]
            t = datetime.strptime(start_string, '%H:%M:%S')
            start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            # Duration
            duration_string = line.split('Dur:')[-1].split()[0]
            t = datetime.strptime(duration_string, '%H:%M:%S')
            duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            # Altitude
            altitude = line.split(':')[1].split()[0].strip()
        else:
            start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            # Duration
            t = datetime.strptime(l[2].split()[-1], '%H:%M:%S')
            duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            # Altitude
            altitude = l[3].split(':')[-1].split()[0].strip()
        finally:
            return leg_num, description, start, duration, altitude


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
        self.takeoff_runway = 0
        self.takeoff_latitude = ''
        self.takeoff_longitude = ''

    def __str__(self):
        s = '\nPlane:\n'
        s += '\tTakeoff: {0:s}, {1:s}, Runway {2:d}\n'.format(self.takeoff_latitude,
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


def summary_object(obj):
    attrs = vars(flight)
    s = []
    for item in attrs.items():
        s.append('{0}: {1}'.format(item[0], item[1]))
    return '\n'.join(s)


if __name__ == '__main__':
    loc = '/home/jrvander/code/SOFIACruiseTools/inputs/'
    filenames = glob.glob(loc + '*mis')
    tags = ['Filename:', 'Flight', 'Leg', 'UTC', 'Comment:',
            '============================= ', 'Airport:']
    for fname in filenames:
        # fname = loc + '201803_FI_DIANA_SCI.mis'

        print(fname.split('/')[-1])
        flight = FlightProfile()
        with open(fname, 'r') as f:
            data = f.read()
        flight.hash = hashlib.sha1(data).hexdigest()
        sections = re.split(r'\n{2}', data)
        for section in sections:
            flight.parse_section(section.strip())

        print(flight)
        for i, l in enumerate(flight.legs):
            print(l)

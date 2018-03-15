


from __future__ import print_function
import pandas as pd
import re
import glob
from datetime import datetime, timedelta


# In[2]:


loc = '/home/jrvander/code/SOFIACruiseTools/inputs/'
filename = '201803_FI_DIANA_SCI.mis'


# In[3]:


fname = loc+filename
with open(fname,'r') as f:
    data = f.read()


# In[17]:


class ParseError(Exception):
    def __init__(self,value):
        self.value = value
    
    def __str__(self):
        return(repr(self.value))


# In[29]:



# In[2]:


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


# In[3]:


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


# In[4]:


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


# In[5]:


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
        txtStr = "%s to %s, %d flight legs." %                 (self.origin, self.destination, self.num_legs)
        txtStr += "\nTakeoff at %s\nLanding at %s\n" %                  (self.takeoff, self.landing)
        txtStr += "Flight duration of %s including %s observing time\n" %                  (str(self.flight_time), self.obs_time)
        txtStr += "Filename: %s" % self.filename

        return txtStr


# In[6]:


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



# In[27]:


def identify_science_leg(section):
    '''
    Identifies the leg type.
    Returns the leg type: 'science','takeoff','landing','dead','other'
    '''
    print('\nSection: ',section)
    lines = section.split('\n')
    print('Lines: ',lines)
    # Get the leg number
    try:
        leg_num = int(lines[0].split()[1])
    except IndexError:
        print('Cannot parse leg_num from: ')
        print(lines[0])
        raise ParseError(lines[0])
    else:
        description = lines[0][lines[0].find('('):lines[1].find(')')+1]
        if leg_num==1:
            # First leg is always takeoff
            return 'takeoff'
        elif 'approach' in description.lower():
            # Landing leg
            return 'landing'
        elif 'dead' in description.lower(): 
            # One way to identify a dead leg
            return 'dead'
        elif lines[1].startswith('ObspID'):
            # As far as I can tell, only science legs have the ObspID field
            return 'science'
        else:
            return 'other'


# In[8]:


def parse_mission(section,flight,tag):
    lines = section.split('\n')
    if tag=='Flight':
        # This flight plan has an additional line containing the flight plan id
        # Don't care about this, so pop it off
        lines.pop(0)
    # First line: Airport, Runway, Legs, Mach
    l = lines[0].split()
    flight.origin = l[1]
    flight.drunway = l[3]
    flight.num_legs = int(l[5])
    flight.mach = float(l[7])

    # Second line: Takeoff
    takeoff_str = lines[1][9:].strip()
    print('takeoff_str = ',takeoff_str)
    flight.takeoff = datetime.strptime(takeoff_str,'%Y-%b-%d %H:%M:%S %Z')

    # Third line: Observing time, Flight time
    l = lines[2].split()
    observing_str = l[2]
    t = datetime.strptime(observing_str, '%H:%M:%S')
    flight.obs_time = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    flight_str = l[5]
    t = datetime.strptime(flight_str, '%H:%M:%S')
    flight.flight_time = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    # Forth line: landing timestamp, landing airport
    l = lines[3].split()
    landing_str = '{0:s} {1:s} {2:s}'.format(l[1],l[2],l[3])
    flight.landing = datetime.strptime(landing_str,'%Y-%b-%d %H:%M:%S %Z')
    flight.destination = l[5]

    # Fifth line: sunset time, sunset az, sunrise time, sunrise az
    l = lines[4].split()
    flight.sunrise = datetime.strptime(l[1],'%H:%M:%S')
    flight.sunset = datetime.strptime(l[6],'%H:%M:%S')



def parse_section(section,flight):
    tag = section.split()[0]
    if tag=='Filename:':
        filename = section.split()[1]
        flight.filename = filename
    elif tag=='Flight' or tag=='Airport':
        # Mission summary
        parse_mission(section,flight,tag)
    elif tag=='Leg':
        # This section describes a leg
        # There are different legs: Takeoff, Landing, Dead, Science, Other
        leg_type = identify_science_leg(section)
        leg = LegProfile()
        if leg_type=='takeoff':
            parse_takeoff_leg(section,leg)
        elif leg_type=='landing':
            parse_landing_leg(section,leg)
        elif leg_type=='dead':
            parse_dead_leg(section,leg)
        elif leg_type=='science':
            parse_science_leg(section,leg)
        else:
            parse_other_leg(section,leg)
            

def parse_leg_first_line(line, leg, size):
    '''
    The first line of a leg is the same format
    '''
    # Line 1: Leg number, start time, duration, altitude
    # Formatted to fields 20 characters wide
    print('Parsing first line: ',line)
    l = split_string_size(line.strip(),size)
    #l = [line[i:i+size].strip() for i in range(0,len(line),size)]
    leg.leg_num = int(l[0].split()[1])
    # Start time
    t = datetime.strptime(l[1].split()[1], '%H:%M:%S')
    leg.start = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    # Duration
    t = datetime.strptime(l[2].split()[2], '%H:%M:%S')
    leg.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    # Altitude
    leg.plane.altitude = l[3].split(':')[1].split()[0].strip()


def parse_science_leg(section,leg):
    ''' Parses a science leg, filling LegProfile leg '''
    lines = section.split('\n')
    size = 20
    
    leg.leg_type = 'science'
    parse_leg_first_line(lines[0], leg, size)
    
    # Line 2: ObspID, Blk, Priotity, Obs Duration
    line = lines[1].strip()
    l = split_string_size(line,size)
    l = [line[i:i+size].strip() for i in range(0,len(line),size)]
    # ObspID
    leg.obs_plan = l[0].split(':')[1].strip()
    # Obs blk
    leg.obs_blk = l[1].split(':')[1].strip()
    # Priority
    leg.priority = l[2].split(':')[1].strip()
    # Observation duration
    try:
        obs_str = (l[3][l[3].index(':')+1:]).strip()
    except ValueError:
        leg.obs_dur = 'Unknown'
    else:
        t = datetime.strptime(obs_str, '%H:%M:%S')
        leg.obs_dur = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    
    # Line 3: Target, RA, DEC, Equinox
    line = lines[2].strip()
    l = split_string_size(line,size)
    # Target
    try:
        target_str = l[0].split(':')[1].strip()
    except (IndexError, AttributeError):
        target_str = 'Unknown'
    leg.astro.target = target_str

    # RA
    try:
        ra_str = l[1].split(':')[1].strip()
    except (IndexError, AttributeError):
        ra_str = 'Unknown'
    leg.astro.ra = ra_str
    # Dec
    try: 
        dec_str = l[2].split(':')[1].strip()
    except (IndexError, AttributeError):
        dec_str = 'Unknown'
    leg.astro.dec = dec_str
    # Equinox
    try:
        epoch_str = l[3].split(':').strip()
    except (IndexError, AttributeError):
        epoch_str = 'Unknown'
    leg.astro.epoch = epoch_str
    
    # Line 4a: Careful, there are multiple versions
    # If object is non-siderial, this line just as naif_id.
    # If the object is siderial, this line is missing
    if lines[3].strip().startswith('NAIF ID'):
        line = lines.pop(3)
        leg.astro.naif_id = int(line.split(':')[1])
        leg.astro.nonsiderial = True
        leg.astro.non_sid = True
    
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
        l = re.findall(pattern,line)
        # First field: elevation range:
        leg.plane.elevation_range = [float(i) for i in l[0].split(',')]
        # Second field: ROF range:
        leg.plane.rof_range = [float(i) for i in l[1].split(',')]
        # Third field: ROF rate range:
        leg.plane.rof_rate_range = [float(i) for i in l[2].split(',')]
        # ROF rate unit:
        leg.plane.rof_rate_unit = line.split(':')[3].split()[2].strip()
        # FPI is the last field:
        leg.plane.fpi = int(line.split(':')[-1])
        
        # Line 5: Moon angle, Moon illumination, True heading range, 
        # True heading rate range, True heading rate unit
        line = lines[4].strip()
        # Moon angle:
        leg.astro.moon_angle = int(line.split(':')[1].split()[0])
        # Moon illumination
        leg.astro.moon_illum = line.split(':')[2].split()[0]
        # True heading range
        # This and true heading rate range use the same bracket notation as
        # ROF rate and ROF rate range
        l = re.findall(pattern,line)
        # True heading range
        leg.plane.true_heading_range = [float(i) for i in l[0].split(',')]
        # True heading rate range
        leg.plane.true_heading_rate_range = [float(i) for i in l[1].split(',')]
        # True heading rate unit
        leg.plane.true_heading_rate_unit = line.split()[-1]
    
    else:
        # Old format 
        # Line 4: Elevation range, ROF range, ROF rate range, 
        # ROF range unit, Moon angle
        line = lines[3].strip()
        # Use the same bracket searching for the ranges
        pattern = re.compile(r'\[(.*?)\]')
        l = re.findall(pattern,line)
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
        




def parse_takeoff_leg(section, leg):
    """
    Parses a takeoff leg
    """

    lines = section.strip().split('\n')
    size = 20

    # Line 1: Start, duration, altitude
    leg.leg_type = 'takeoff'
    parse_leg_first_line(lines[0], leg, size)

    # Line 2: Runway, ending latitude, ending longitude, sunset, sunset Az
    l = split_string_size(lines[1].strip(), size)
    # First field: Runway
    leg.plane.drunway = l[0].split()[1].strip()
    # Second field: Ending latitude
    leg.plane.takeoff_latitude = l[1].split(':')[1].strip()
    # Third field: Ending longitude
    leg.plane.takeoff_longitude = l[2].split(':')[1].strip()
    # Forth field: Sunset time
    t = datetime.strptime(l[3].split()[1], '%H:%M:%S')
    leg.plane.sunset = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    # Fifth field: Sunset azimuth
    leg.plane.sunset_az = float(l[4].split(':')[1])
    

def parse_other_leg(section, leg):
    '''
    Parse other leg.
    Don't care about this, so don't do anything
    '''
    return


    
def split_string_size(line, size):
    ''' Splits line into chunks of length size '''
    return [line[i:i+size].strip() for i in range(0,len(line),size)]


# In[125]:


#filenames = glob.glob(loc+'*mis')
#tags = 'Filename: Flight Leg UTC Comment: ============================= Airport:'.split()
#for fname in filenames:
#    #fname = loc+'201803_FI_DIANA_SCI.mis'
#    flight = FlightProfile()
#    with open(fname,'r') as f:
#        data = f.read()
#    sections = re.split(r'\n{2}',data)
#    for section in sections:
#        #print('\nSection:', section)
#        lines = section.strip().split('\n')
#        #print('Number of lines: ',len(lines))
#        #print('First line: ',lines[0])
#        if 'RA' in section and 'DEC' in section:
#            if len(lines)>4 and 'FPI' not in section:
#                print('Missing FPI in {0:s}'.format(fname))
#            elif len(lines)==4 and 'FPI' in section:
#                print('Found FPI in {0:s}'.format(fname))


def parse_header(head):
    # Split fields
    fields = [i.strip() for i in re.split(r'\s{2}',h) if i]
    print(fields[0])
    leg_num = int(fields[0].split()[1])
    pattern = re.compile(r'\((.*?)\)')
    #pattern = re.compile(r'[(]')
    #pattern = re.compile('Leg')
    target = pattern.search(fields[0]).group(1)
    target = fields[0][fields[0].find('(')+1:fields[0].find(')')]
    props = {}
    for field in fields[1:]:
        label = field.split(':')[0]
        if label=='ROF':
            field = [i.strip() for i in re.split(r'[:,\[\]]',s) if i.strip()]
            props[field[0]] = field[1:3]
            props[label+field[3]] = field[4:6]
                
        else:
            value = field.split(':')[1].strip()
            props[label] = value    
        
    print(leg_num,target)
    print(props)


if __name__=='__main__':
    loc = '/home/jrvander/code/SOFIACruiseTools/inputs/'
    filenames = glob.glob(loc+'*mis')
    tags = 'Filename: Flight Leg UTC Comment: ============================= Airport:'.split()
    for fname in filenames:
        fname = loc+'201803_FI_DIANA_SCI.mis'
        flight = FlightProfile()
        with open(fname,'r') as f:
            data = f.read()
        sections = re.split(r'\n{2}',data)
        for section in sections:
            parse_section(section.strip(), flight)
        print(flight.summarize())
        
        break    


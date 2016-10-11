# -*- coding: utf-8 -*-
"""
Created on Sat Oct  8 01:23:08 2016

@author: rhamilton
"""

# You'll probably have to pip install this one, but by jove it's worth it
import untangle
import numpy as np


class AOR(object):
    def __init__(self):
        self.propid = ''
        self.title = ''
        self.pi = ''
        self.observations = []


class Observation(object):
    def __init__(self):
        self.aorid = ''
        self.duration = 0.
        self.overhead = 0.
        self.instrument = ''
        self.spectel1 = ''
        self.spectel2 = ''
        self.target = ''
        self.coord1 = 0.
        self.coord2 = 0.
        self.coordsys = ''
        self.coord1PM = 0.
        self.coord2PM = 0.
        self.coordepoch = ''
        self.obsplanmode = ''
        self.GIcomments = ''


infile = './70_0402.aor'
aorfile = untangle.parse(infile)

# More or less a standard path to get down into the useful stuff
aors = aorfile.AORs.list
thisAOR = AOR()
thisAOR.pi = aors.ProposalInfo.ProposalPI.cdata
thisAOR.title = aors.ProposalInfo.ProposalTitle.cdata
thisAOR.propid = aors.ProposalInfo.ProposalID.cdata

print "%s: %s, %s" % (thisAOR.propid, thisAOR.title, thisAOR.pi)

for each in aors.vector.Request:
    obs = Observation()
    # Common to each AOR
    obs.aorid = each.aorID.cdata
    obs.duration = np.float(each.est.duration.cdata)
    obs.overhead = np.float(each.overhead.cdata)

    # Not always comments in there, depends on the GI
    try:
        obs.GIcomments = each.observerComment
    except IndexError:
        obs.GIcomments = None

    tar = each.target
    obs.target = tar.name.cdata
    obs.coord1 = np.float(tar.position.lat.cdata)
    obs.coord1PM = np.float(tar.position.pm.latPm.cdata)
    obs.coord2 = np.float(tar.position.lon.cdata)
    obs.coord2PM = np.float(tar.position.pm.lonPm.cdata)
    obs.coordepoch = tar.position.epoch.cdata
    obs.coordsys = tar.position.coordSystem.coodSysName

    # Was undefined in the example AOR I'm working from, but depends on the GI
    latts = each.target.locationAttributes
    tatts = each.target.targetAttributes

    inst = each.instrument
    obs.spectel1 = inst.data.InstrumentSpectralElement1.cdata
    obs.spectel2 = inst.data.InstrumentSpectralElement2.cdata
    obs.obsplanmode = inst.data.ObsPlanMode.cdata

    # Instrument specific stuff
    obs.instrument = inst.data.InstrumentName.cdata
    print "    %s %s: %s, " % (obs.instrument, obs.aorid, obs.target),
    print "%s + %s, %s" % (obs.spectel1, obs.spectel2, obs.obsplanmode)

    thisAOR.observations.append(obs)

print "%d observations in this AOR" % (len(thisAOR.observations))

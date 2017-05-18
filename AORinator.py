# -*- coding: utf-8 -*-
"""
Created on Sat Oct  8 01:23:08 2016

@author: rhamilton
"""

import sys
# You'll probably have to pip install this one, but by jove it's worth it
import untangle
import numpy as np

import astropy.units as apu
import astropy.coordinates as apc
import astropy.table as aptable
import astropy.io.ascii as apascii


def underliner(instr, char="="):
    """
    Given a string, return an "=" underline of the same length.
    """
    slen = len(instr)
    ostr = char * slen
    return ostr


class AOR(object):
    def __init__(self):
        self.propid = ''
        self.title = ''
        self.pi = ''
        self.observations = {}

    def summarize(self, output='reST'):
        if output == 'reST':
            txtSumm = "%s\n%s\n%s, %s" % (self.propid, underliner(self.propid),
                                          self.title, self.pi)
        else:
            txtSumm = "%s: %s, %s\n" % (self.propid, self.title, self.pi)
            txtSumm += "%d observations in this AOR" % (len(self.observations))

        return txtSumm


class Observation(object):
    def __init__(self):
        self.aorid = ''
        self.aname = ''
        self.duration = 0.
        self.overhead = 0.
        self.instrument = ''
        self.spectel1 = ''
        self.spectel2 = ''
        self.target = ''
        self.tartype = 'Sidereal'
        self.order = 1
        self.coord1 = 0.
        self.coord2 = 0.
        self.coordsys = ''
        self.coord1PM = 0.
        self.coord2PM = 0.
        self.naifID = 0
        self.naifName = ''
        self.coordepoch = ''
        self.obsplanmode = ''
        self.obsplanconfig = ''
        self.nodtype = ''
        self.GIcomments = ''
        self.repeats = 1

        # HAWC+ Chop-Nod (C2N NMC) options
        self.chopcrsys = 'Sky'
        self.chopangle = 0.
        self.chopanglesofia = 0.
        self.chopthrow = 0.
        self.nodcrsys = 'Sky'
        self.nodangle = 0.
        self.nodanglesofia = 0.
        self.nodthrow = 0.
        self.nodtime = 0.
        self.chopfreq = 0.
        self.choptype = '2_point'
        self.chopsrc = 'External'
        self.choponfpa = False

        # HAWC+ Dither options
        self.ditherpatt = '4_Point'
        self.dithercoord = 'Sky'
        self.ditherstretchx = 0.
        self.ditherstretchy = 0.
        self.ditherscale = 0.
        # TODO: support the DitherOffset keys specifically.

        # HAWC+ Polarization options
        self.hwpstep = 0.
        self.hwpini = 0.
        self.hwpnum = 0.

        # HAWC+ scan general options
        self.scantype = ''
        self.scananglow = 0.
        self.scananghigh = 0.
        self.scanrate = 0.

        # HAWC+ Box scan options
        self.scansize = 0.
        self.scanstepsize = 0.
        self.scansteps = 0.
        self.scancross = True

        # HAWC+ Lissajous scan options
        self.scanamp = 0.
        self.scanfreq = 0.
        self.scanphase = 0.

    def summarize(self, output='reST'):
        if output == 'reST':
            pass
        else:
            txtSumm = "%s %s: '%s' %s\n" % (self.instrument, self.aorid,
                                          self.aname, self.target)
            txtSumm += "%s + %s, %s\n" % (self.spectel1,
                                        self.spectel2,
                                        self.obsplanconfig)

        return txtSumm


def parseAOR(infile, summarize=False):
    """
    """
#    print "Parsing %s" % (infile)

    try:
        aorfile = untangle.parse(infile)
    except ImportError:
        print "FATAL ERROR: Install the 'untangle' python library!"
        sys.exit(-1)
    except IOError:
        print "FATAL ERROR: File not found!"
        sys.exit(-1)

    # More or less a standard path to get down into the useful stuff
    aors = aorfile.AORs.list
    thisAOR = AOR()
    thisAOR.pi = aors.ProposalInfo.ProposalPI.cdata
    thisAOR.title = aors.ProposalInfo.ProposalTitle.cdata
    thisAOR.propid = aors.ProposalInfo.ProposalID.cdata

    for each in aors.vector.Request:
        obs = Observation()
        # Common to each AOR
        obs.aorid = each.aorID.cdata
        obs.aname = each.title.cdata
        obs.duration = np.float(each.est.duration.cdata)
        obs.overhead = np.float(each.overhead.cdata)

        # Not always comments in there, depends on the GI
        try:
            obs.GIcomments = each.observerComment
        except IndexError:
            obs.GIcomments = None

        tar = each.target
        tartype = tar['class']
        obs.target = tar.name.cdata
        # added to help with confluence exporting
        obs.target = obs.target.replace('[', '').replace(']', '')

        if tartype == "SofiaTargetMovingSingle":
            obs.naifID = np.int(tar.ephemeris.naifID.cdata)
            obs.naifName = tar.ephemeris.naifName.cdata
            obs.tartype = 'Non-Sidereal'
        elif tartype == "SofiaTargetFixedSingle":
            obs.coord1 = np.float(tar.position.lat.cdata)
            obs.coord1PM = np.float(tar.position.pm.latPm.cdata)
            obs.coord2 = np.float(tar.position.lon.cdata)
            obs.coord2PM = np.float(tar.position.pm.lonPm.cdata)
            obs.coordepoch = tar.position.epoch.cdata
            obs.coordsys = tar.position.coordSystem.coodSysName

            sc = apc.SkyCoord(ra=obs.coord2, dec=obs.coord1, unit='deg',
                              equinox=obs.coordepoch)

            hms = "%02dh%02dm%05.2fs" % (sc.ra.hms)
            obs.coord2 = hms
            obs.coord1 = sc.dec.to_string(alwayssign=True,
                                          pad=True, precision=2)
            obs.tartype = 'Sidereal'

        # Was undefined in the example AOR I'm working from
        #   but its usefulness largely depends on the GI
        latts = each.target.locationAttributes
        tatts = each.target.targetAttributes

        inst = each.instrument.data
        obs.order = inst.order.cdata
        obs.spectel1 = inst.InstrumentSpectralElement1.cdata
        obs.spectel2 = inst.InstrumentSpectralElement2.cdata

        # Instrument specific stuff
        obs.instrument = inst.InstrumentName.cdata
        if obs.instrument == "HAWC_PLUS":
            obs = parseHAWCpObs(inst, obs)

        # Stuff it into the base dict
        thisAOR.observations[obs.aorid] = obs

    return thisAOR


def parseHAWCpObs(root, aobs):
    """
    Given an untangle'd object representing a HAWC+ AOR, unpack it
    """
    aobs.obsplanmode = root.ObsPlanMode.cdata
    aobs.obsplanconfig = root.ObsPlanConfig.cdata
    aobs.repeats = np.int(root.Repeat.cdata)
    if aobs.obsplanmode == "OTFMAP":
        # NOTE: Not currently supporting chopped scans
        # Parameters comment to both scan types
        aobs.scantype = root.ScanType.cdata
        aobs.scananglow = np.float(root.ScanAngleRange_Low.cdata)
        aobs.scananghigh = np.float(root.ScanAngleRange_High.cdata)
        aobs.scanrate = np.float(root.ScanRate.cdata)
        aobs.exptime = np.float(root.TotalTime.cdata)
        if aobs.scantype == "Box":
            aobs.scanstepsize = np.float(root.ScanStepSize.cdata)
            aobs.scansteps = np.float(root.ScanSteps.cdata)
            aobs.scancross = np.bool(root.ScanCross.cdata)
            aobs.scansize = np.float(root.ScanSize.cdata)
            aobs.subscans = np.int(root.NumSubscan.cdata)
        elif aobs.scantype == "Lissajous":
            aobs.scanamp = np.float(root.ScanAmplitude.cdata)
            aobs.scanfreq = np.float(root.ScanFreq.cdata)
            aobs.scanphase = np.float(root.ScanPhase.cdata)
#        print aobs.aname, aobs.aorid, aobs.target, aobs.instrument,
#        print aobs.obsplanconfig, aobs.obsplanmode, aobs.scantype
    elif aobs.obsplanmode == "C2N":
        # Parameters common to both total_intensity and polarization obs
        aobs.nodtype = root.NodType.cdata
        if aobs.nodtype == "Nod_Match_Chop":
            # General chopping stuff...might work for other instruments
            aobs.chopcrsys = root.ChopAngleCoordinate.cdata
            aobs.chopangle = np.float(root.ChopAngle.cdata)
            aobs.chopanglesofia = (180. - aobs.chopangle)
            aobs.chopthrow = np.float(root.ChopThrow.cdata)
            aobs.chopfreq = np.float(root.ChopFreq.cdata)
            aobs.choptype = root.ChopType.cdata
            aobs.chopsrc = root.ChopSyncSrc.cdata
            aobs.choponfpa = np.bool(root.ChopOnFPA.cdata)
            aobs.nodcrsys = root.NodAngleCoordinate.cdata
            aobs.nodangle = np.float(root.NodAngle.cdata)
            aobs.nodanglesofia = (aobs.chopanglesofia - 180.)
            aobs.nodthrow = np.float(root.NodThrow.cdata)
            aobs.nodtime = np.float(root.NodTime.cdata)

            # Dithering
            aobs.ditherpatt = root.DitherPattern.cdata
            aobs.dithercoord = root.DitherCoord.cdata
            aobs.ditherstretchx = np.float(root.DitherOffsetX.cdata)
            aobs.ditherstretchy = np.float(root.DitherOffsetY.cdata)
            aobs.ditherscale = np.float(root.DitherScale.cdata)
            if aobs.obsplanconfig == "TOTAL_INTENSITY":
                # Nothing further specific for total intensity observations
                pass
            elif aobs.obsplanconfig == "POLARIZATION":
                aobs.hwpstep = np.float(root.StepHWP.cdata)
                aobs.hwpini = np.float(root.InitialHWP.cdata)
                aobs.hwpnum = np.int(root.NumHWP.cdata)

#        print aobs.aname, aobs.aorid, aobs.target, aobs.instrument,
#        print aobs.obsplanconfig, aobs.obsplanmode, aobs.nodtype
    return aobs


def summarizeObsGroups(obsgroups, output='rst'):
    """
    Given a dict of sorted AORs, make a nice little table about each group
    """
    # Top level groups; should be main distinct observing modes
    #   For HAWC+: TOTAL_INTENSITY and POLARIZATION
    tkeys = obsgroups.keys()
    for okey in tkeys:
        thisgroup = obsgroups[okey]
        if type(thisgroup) == dict:
            # Next level - variations on the main observing modes
            #   For HAWC+: TOTAL_INTENSITY OTFMAP or C2N
            for ikey in thisgroup.keys():
                innergroup = thisgroup[ikey]
                # Innermost level - variations on a variation of a main mode
                #  FOR HAWC+: TOTAL_INTENSITY OTFMAP ScanVariants
                if type(innergroup) == dict:
                    for iikey in innergroup.keys():
                        final = innergroup[iikey]
                        if type(final) == list:
                            print ""
                            print "**" + okey, ikey, iikey + "**\n"
                            if output == 'rst':
                                hawcAORreSTer(innergroup[iikey], ikey, iikey)
                            elif output == 'confluence':
                                hawcAORConfluencer(innergroup[iikey], ikey,
                                                   iikey)
                            elif output == 'tab':
                                hawcAORtabber(innergroup[iikey], ikey,
                                              iikey)

                        else:
                            print ""
                            print "**" + okey, ikey, iikey + "**\n"
                            if output == 'rst':
                                hawcAORreSTer(innergroup, ikey, iikey)
                            elif output == 'confluence':
                                hawcAORConfluencer(innergroup, ikey, iikey)
                            elif output == 'tab':
                                hawcAORtabber(thisgroup, ikey, iikey)
                else:
                    print ""
#                    print "**" + okey, ikey, innergroup + "**\n"
        elif type(thisgroup) == list:
            # Simple modes - a mode name, and a list of matching AORs
            #  For HAWC+: POLARIZATION C2N
            print ""
            print "**" + okey + "**\n"
            if output == "rst":
                hawcAORreSTer(thisgroup, 'POLARIZATION')
            elif output == 'confluence':
                hawcAORConfluencer(thisgroup, 'POLARIZATION')
            elif output == 'tab':
                hawcAORtabber(thisgroup, 'POLARIZATION')


def hawcAORConfluencer(AORgroup, key1, key2=''):
    """
    Given a sorted grouping of AORs in a dictionary, print a Confluence
    formatted table for use elsewhere.
    """
    if key1 == "POLARIZATION" and AORgroup != []:
        print "||*AORID*",
        print "||*AOR Name*",
        print "||*Target*||*Spectel1*||*Spectel2",
        print "||*RA (2000)*||*Dec (2000)*",
        print "||*ExpTime*",
        print "||*ChopSys*||*ChopAngle*||*NodAngle*||*ChopThrow*",
        print "||*DthScale*||"
        for taor in AORgroup:
            os = "|%s|%s|%s|%s|%s|%s|%s|%05.2f|" %\
                (taor.aorid, taor.aname, taor.target,
                 taor.spectel1, taor.spectel2, taor.coord2, taor.coord1,
                 taor.duration-taor.overhead)
            os += "%s|%04.1f|%04.1f|%04.1f|%02.1f|" %\
                  (taor.chopcrsys, taor.chopangle,
                   taor.nodangle, taor.chopthrow, taor.ditherscale)
            print os
    if key1 == 'OTFMAP' and AORgroup != []:
        if key2 == 'Box':
            print "||*AORID*",
            print "||*AOR Name*",
            print "||*Target*||*Spectel1*||*Spectel2",
            print "||*RA (2000)*||*Dec (2000)*",
            print "||*ExpTime*",
            print "||*ScanLength*||*StepSize*||*NLines*||*ScanIters*",
            print "||*AngLow*||*AngHigh*|",
            print "||*SubScans*||"
            for taor in AORgroup:
                os = "|%s|%s|%s|%s|%s|%s|%s|%05.2f|" %\
                    (taor.aorid, taor.aname, taor.target,
                     taor.spectel1, taor.spectel2, taor.coord2,
                     taor.coord1,
                     taor.duration-taor.overhead)
                os += "%04.1f|%03.1f|%03.1f|%02d|%+03.1f|%+03.1f|%02d|" %\
                    (taor.scansize, taor.scanstepsize, taor.scansteps,
                     taor.repeats, taor.scananglow, taor.scananghigh,
                     taor.subscans)
                print os
        if key2 == 'Lissajous':
            print "||*AORID*",
            print "||*AOR Name*",
            print "||*Target*||*Spectel1*||*Spectel2",
            print "||*RA (2000)*||*Dec (2000)*",
            print "||*ExpTime*",
            print "||*ScanAmp*||*ScanIters*|"
            for taor in AORgroup:
                os = "|%s|%s|%s|%s|%s|%s|%s|%05.2f|" %\
                    (taor.aorid, taor.aname, taor.target,
                     taor.spectel1, taor.spectel2, taor.coord2,
                     taor.coord1,
                     taor.duration-taor.overhead)
                os += "%04.1f|%02d|" %\
                    (taor.scanamp, taor.repeats,
                     taor.scananglow, taor.scananghigh)
                print os


def hawcAORreSTer(AORgroup, key1, key2='', outie=sys.stdout):
    """
    Given a sorted grouping of AORs in a dictionary, print a reST
    formatted blob of text for use elsewhere.
    """
    if key1 == "POLARIZATION" and AORgroup != []:
        hed = ["AORID", "AOR Name", "Target",
               "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
               "ExpTime", "ChopSys", "ChopAngle", "Nod Angle",
               "ChopAngle-WoN", "NodAngle-WoN",
               "ChopThrow", "DthScale"]
        tabdat = []
        for taor in AORgroup:
            tabdat.append([taor.aorid, taor.aname, taor.target,
                          taor.spectel1, taor.spectel2,
                          taor.coord2, taor.coord1,
                          taor.duration-taor.overhead,
                          taor.chopcrsys, taor.chopangle, taor.nodangle,
                          taor.chopanglesofia, taor.nodanglesofia,
                          taor.chopthrow, taor.ditherscale])
        tabbie = aptable.Table(rows=tabdat, names=hed)
        tabbie.write(outie, format='ascii.rst')
        print ""
    if key1 == 'OTFMAP' and AORgroup != []:
        if key2 == 'Box':
            hed = ["AORID", "AOR Name", "Target",
                   "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
                   "ExpTime", "ScanRate", "ScanLength", "StepSize", "NLines",
                   "ScanIters", "AngLow", "AngHigh", "SubScans"]
            tabdat = []
            for taor in AORgroup:
                tabdat.append([taor.aorid, taor.aname, taor.target,
                               taor.spectel1, taor.spectel2, taor.coord2,
                               taor.coord1, taor.duration-taor.overhead,
                               taor.scanrate,
                               taor.scansize, taor.scanstepsize,
                               taor.scansteps, taor.repeats,
                               taor.scananglow, taor.scananghigh,
                               taor.subscans])
            tabbie = aptable.Table(rows=tabdat, names=hed)
            tabbie.write(outie, format='ascii.rst')
            print ""
        if key2 == 'Lissajous':
            hed = ["AORID", "AOR Name", "Target",
                   "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
                   "ExpTime", "ScanRate", "ScanAmp", "ScanIters", "ScanPhase"]
            tabdat = []
            for taor in AORgroup:
                tabdat.append([taor.aorid, taor.aname, taor.target,
                               taor.spectel1, taor.spectel2, taor.coord2,
                               taor.coord1, taor.duration-taor.overhead,
                               taor.scanrate,
                               taor.scanamp, taor.repeats, taor.scanphase])
            tabbie = aptable.Table(rows=tabdat, names=hed)
            tabbie.write(outie, format='ascii.rst')
            print ""


def hawcAORtabber(AORgroup, key1, key2=''):
    """
    Given a sorted grouping of AORs in a dictionary, print a tab seperated
    formatted blob of text for use elsewhere.
    """
    if key1 == "POLARIZATION" and AORgroup != []:
        hed = ["AORID", "AOR Name", "Target",
               "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
               "ExpTime", "ChopSys", "ChopAngle",
               "NodAngle", "ChopThrow", "DthScale"]
        tabdat = []
        for taor in AORgroup:
            tabdat.append([taor.aorid, taor.aname, taor.target,
                          taor.spectel1, taor.spectel2,
                          taor.coord2, taor.coord1,
                          taor.duration-taor.overhead,
                          taor.chopcrsys, taor.chopangle,
                          taor.nodangle, taor.chopthrow, taor.ditherscale])
        tabbie = aptable.Table(rows=tabdat, names=hed)
        tabbie.write(sys.stdout, format='ascii.csv')
        print ""
    if key1 == 'OTFMAP' and AORgroup != []:
        if key2 == 'Box':
            hed = ["AORID", "AOR Name", "Target",
                   "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
                   "ExpTime", "ScanRate", "ScanLength", "StepSize", "NLines",
                   "ScanIters", "AngLow", "AngHigh", "SubScans"]
            tabdat = []
            for taor in AORgroup:
                tabdat.append([taor.aorid, taor.aname, taor.target,
                               taor.spectel1, taor.spectel2, taor.coord2,
                               taor.coord1, taor.duration-taor.overhead,
                               taor.scanrate,
                               taor.scansize, taor.scanstepsize,
                               taor.scansteps, taor.repeats,
                               taor.scananglow, taor.scananghigh,
                               taor.subscans])
            tabbie = aptable.Table(rows=tabdat, names=hed)
            tabbie.write(sys.stdout, format='ascii.csv')
            print ""
        if key2 == 'Lissajous':
            hed = ["AORID", "AOR Name", "Target",
                   "Spectel1", "Spectel2", "RA (2000)", "Dec (2000)",
                   "ExpTime", "ScanRate", "ScanAmp", "ScanIters", "ScanPhase",
                   "AngLow", "AngHigh"]
            tabdat = []
            for taor in AORgroup:
                tabdat.append([taor.aorid, taor.aname, taor.target,
                               taor.spectel1, taor.spectel2, taor.coord2,
                               taor.coord1, taor.duration-taor.overhead,
                               taor.scanrate,
                               taor.scanamp, taor.repeats, taor.scanphase,
                               taor.scananglow, taor.scananghigh])
            tabbie = aptable.Table(rows=tabdat, names=hed)
            tabbie.write(sys.stdout, format='ascii.csv')
            print ""


def HAWCAORSorter(infile, aorids=[], output='rst', silent=False):
    """
    Given an AOR file and an optional list of AOR IDs to summarize,
    parse the AOR and return either all or the specific AOR IDs in a nicely
    summarized text format for insertion into something else.

    Returns the full AOR object as well as the sorted dict of AOR types.
    """
    # Actually parse the file first
    aor = parseAOR(infile)

    # There are many total_intensity variants, but only one for polarization
    hawcgroups = {'TOTAL_INTENSITY': {'C2N': [],
                                      'OTFMAP': {
                                                 'Box': [],
                                                 'Lissajous': []
                                                 }
                                      },
                  'POLARIZATION': []}

    if aorids == []:
        aorids = aor.observations.keys()

    for aorid in aorids:
        taor = aor.observations[aorid]
        # Now try to group things via observing modes to make printing easier
        #   (will be specific for each instrument)
        if taor.obsplanconfig == 'POLARIZATION':
            hawcgroups[taor.obsplanconfig].append(taor)
        elif taor.obsplanconfig == 'TOTAL_INTENSITY' and\
                taor.obsplanmode == 'C2N':
            hawcgroups[taor.obsplanconfig][taor.obsplanmode].append(taor)
        elif taor.obsplanconfig == 'TOTAL_INTENSITY' and\
                taor.obsplanmode == 'OTFMAP':
            hawcgroups[taor.obsplanconfig][taor.obsplanmode][taor.scantype].append(taor)

    if silent is False:
        print aor.summarize(output='reST')
        summarizeObsGroups(hawcgroups, output=output)

    return aor, hawcgroups

if __name__ == "__main__":
#    infile = '/Users/rhamilton/Desktop/88_0005.aor'
    infile = '/Users/rhamilton/Desktop/88_0006.aor'
#    infile = '/Users/rhamilton/Desktop/04_0138.aor'
#    infile = '/Users/rhamilton/Desktop/04_0059.aor'
    aorids = []
    HAWCAORSorter(infile)
#    aorids = ['88_0005_20', '88_0005_21']
#    HAWCAORSorter(infile, aorids)

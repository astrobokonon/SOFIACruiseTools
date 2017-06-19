# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""

import os
import sys
import getpass
import datetime
import numpy as np
import astropy.table as aptable

import ConfigParser as conf

import newparse as fpmis
import AORinator as aorparse


def underliner(instr, char="="):
    """
    Given a string, return an "=" underline of the same length.
    """
    slen = len(instr)
    ostr = char * slen
    return ostr


def confluencer(infile):
    """
    Given a filenames, parse it one and print the relevant
    observing leg details (as well as takeoff and landing details).

    The formatting is specific to Confluence; to insert the results:
        - In the editor toolbar, click on the + icon
          ("Insert More Content") and choose "{ } Markup"

          - FOR HAWC+ Confluence (5.9.8 or higher)
             - Choose "Confluence Wiki" as the type, and paste the output
               into the lefthand window; it should then preview nicely on right

          - FOR NASA Confluence (5.4.ish)
             - Just paste the output into the box and insert it; it'll preview
               in the main editor window and should be fine
    """

    # Where the magic happens
    flight = fpmis.parseMIS(infile)

    print "*Notes:*\n"
    print "Flight Plan Filename: %s, Vintage: %s" %\
        (flight.filename, flight.saved)

    summy = flight.summarize()
    # Break at the line breaks so we can indent it
    #   (ended up taking out the tabs, but keeping this in case we want it)
    summarylines = summy.split("\n")
    for line in summarylines:
        print "%s" % (line)
    print ""

    for j, oach in enumerate(flight.legs):
        if oach.legtype != "Observing":
            oach.ra = None
            oach.dec = None
            oach.range_rof = [None, None]
            oach.range_elev = [None, None]

        # print the header before the first leg
        if j == 0:
            print "||*Leg Number*",
            print "||*Time Since Takeoff at Leg Start (hrs)*",
            print "||*Leg Type*||*Target*||*RA (2000)*||*Dec (2000)*",
            print "||*Obs Duration*||*Elevation Range*||*ROF Range*||"

        # Should be self explanatory here
        if oach.legtype == "Takeoff" or oach.legtype == "Landing" or\
           oach.legtype == "Observing":
            print "|%02d|%02.1f|%s|%s|%s|%s|%s|%s, %s|%s, %s|" %\
                  (oach.legno, oach.relative_time[0]/60./60.,
                   oach.legtype, oach.target, oach.ra, oach.dec,
                   oach.obsdur, oach.range_elev[0], oach.range_elev[1],
                   oach.range_rof[0], oach.range_rof[1])
    print "----"


def reSTer(infile, title, role='Team', outfile=None):
    """
    Given a MIS file, parse it and print out a summary as well as any
    additional specified AOR details for each leg.

    The formatting is specific to some of the specific (table)
    extensions of reST/Markdown.
    """
    if outfile is None:
        print "FATAL ERROR: No output file specified!"
        sys.exit(-1)
    else:
        f = open(outfile, 'w')

    # Where the magic happens
    flight = fpmis.parseMIS(infile)

    h1 = "%s" % (title)
    f.write(underliner(h1) + '\n')
    f.write(h1 + '\n')
    f.write(underliner(h1) + '\n')
    f.write('\n')
    r1 = "Cheat Sheet generated on %s" % (datetime.datetime.now())
    r1 += " by %s in %s mode \n" % (getpass.getuser(), role)
    f.write(r1)
    f.write('\n')

    if role == 'Team':
        h2 = "Flight Path"
        f.write(h2 + '\n')
        f.write(underliner(h2) + '\n')
        f.write('\n')
        fpimg = infile[:-4] + ".png"
        f.write(".. image:: %s\n" % (fpimg))
        f.write('\n')

    h2 = "Flight Metadata"
    f.write(h2 + '\n')
    f.write(underliner(h2) + '\n')
    f.write("* Plan Filename: %s, Vintage: %s\n" %
                 (flight.filename, flight.saved))
    summy = flight.summarize()
    # Break at the line breaks so we can indent it
    #   (ended up taking out the tabs, but keeping this in case we want it)
    summarylines = summy.split("\n")
    for line in summarylines:
        f.write("* %s\n" % (line))
    f.write('\n')

    # Note that this will grab the table of JUST the
    #   takeoff, observing, and landing leg details
    obstab = []
    obstabhed = []
    for j, oach in enumerate(flight.legs):
        if oach.legtype != "Observing":
            oach.ra = None
            oach.dec = None
            oach.range_rof = [None, None]
            oach.range_elev = [None, None]
            oach.range_rofrt = [None, None]
            oach.range_thdgrt = [None, None]

        # print the header before the first leg
        if j == 0:
            obstabhed = ["Leg Number",
                         "Time Since Takeoff at Leg Start (hrs)",
                         "Leg Type", "ObsBlk", "Target",
                         "RA (2000)", "Dec (2000)",
                         "Obs Duration",
                         "Elevation Range",
                         "ROF Range",
                         "ROF Rate", "THdg Rate"]

        # Should be self explanatory here
        if oach.legtype == "Takeoff" or oach.legtype == "Landing" or\
           oach.legtype == "Observing":
            tabdat = [oach.legno,
                      np.round(oach.relative_time[0]/60./60., 1),
                      oach.legtype, oach.obsblk,
                      oach.target, oach.ra, oach.dec,
                      str(oach.obsdur),
                      str(oach.range_elev)[1:-1],
                      str(oach.range_rof)[1:-1],
                      str(oach.range_rofrt)[1:-1],
                      str(oach.range_thdgrt)[1:-1]]

            obstab.append(tabdat)

    if role == 'Team':
        tabbie = aptable.Table(rows=obstab, names=obstabhed)
        tabbie.write(f, format='ascii.rst')
    elif role == 'TO':
        tabbie = aptable.Table(rows=obstab, names=obstabhed)
        tabbie.write(f, format='ascii.csv')

    if role == 'Team':
        output = 'rst'
    elif role == 'TO':
        output = 'tab'

    # Now go leg-by-leg and print out the gory details.
    if role == 'Team':
        f.write('\n')
        h2 = "Leg Specific Details"
        f.write(h2 + '\n')
        f.write(underliner(h2) + '\n')
        try:
            legconfig = conf.SafeConfigParser()
            legconfig.readfp(open(infile[:-4] + '.conf'))
        except IOError:
            pass
        for j, cleg in enumerate(flight.legs):
            sectitle = "Leg %d" % (cleg.legno)

            data = legconfig.has_section(sectitle)
            if data is True:
                f.write('\n')
                f.write(sectitle + '\n')
                f.write(underliner(sectitle, char="-") + '\n')

                items = legconfig.items(sectitle)
                if legconfig.has_option(sectitle, 'aorfile'):
                    aorfilename = legconfig.get(sectitle, 'aorfile')
                    legconfig.remove_option(sectitle, 'aorfile')
                else:
                    aorfilename = []

                if legconfig.has_option(sectitle, 'aors'):
                    aors = legconfig.get(sectitle, 'aors')
                    aors = aors.split(',')
                    aors = [each.strip() for each in aors]
                    legconfig.remove_option(sectitle, 'aors')
                else:
                    aors = []

                items = legconfig.items(sectitle)
                for each in items:
                    f.write("%s \n  %s\n" % (each[0].capitalize(), each[1]))
                f.write('\n')
                if aorfilename != []:
                    # HAWC+ specific parsing
                    paors, pgroups = aorparse.HAWCAORSorter(aorfilename,
                                                            aorids=aors,
                                                            output=output,
                                                            silent=True)
                    asummary = paors.summarize()
                    f.writelines(asummary)
                    f.write('\n')

                    # HAWC+ Specific gropus
                    if pgroups['POLARIZATION'] != []:
                        f.write('\n')
                        f.write("**POLARIZATION NMC**\n")
                        f.write('\n')
                        # PRINT TABLE
                        aorparse.hawcAORreSTer(pgroups['POLARIZATION'],
                                               'POLARIZATION',
                                               outie=f)

                    if pgroups['TOTAL_INTENSITY'] != []:
                        gshort = pgroups['TOTAL_INTENSITY']['OTFMAP']
                        if gshort['Box'] != []:
                            f.write('\n')
                            f.write("**TOTAL_INTENSITY OTFMAP RASTER**\n")
                            f.write('\n')
                            # PRINT TABLE
                            aorparse.hawcAORreSTer(gshort['Box'],
                                                   'OTFMAP',
                                                   'Box',
                                                   outie=f)
                        if gshort['Lissajous'] != []:
                            f.write('\n')
                            f.write("**TOTAL_INTENSITY OTFMAP LISSAJOUS**\n")
                            f.write('\n')
                            # PRINT TABLE
                            aorparse.hawcAORreSTer(gshort['Lissajous'],
                                                   'OTFMAP',
                                                   'Lissajous',
                                                   outie=f)
    f.close()


#inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/01_201705_HA_EMILY_WX12.mis'
#outfile = '/01_EMILY_Summary.rst'

#inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/02_201705_HA_EAMES_WX12.mis'
#outfile = '/02_EAMES_Summary.rst'

#inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/03_201705_HA_ELAINE_WX12.mis'
#outfile = '/03_Elaine_Summary.txt'

#inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/05_201705_HA_ETHAN_WX12.mis'
#outfile = '/05_Ethan_Summary.txt'

#inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/06_201705_HA_ELMER_1H_LATE_WX12.mis'
#outfile = '/06_Elmer_Summary.txt'

inloc = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/07_201705_HA_EZRA_WX12.mis'
outfile = '/07_Ezra_Summary.txt'

p = os.path.dirname(inloc)
outfile = p + outfile
reSTer(inloc, 'HAWC+ OC5-E', role='Team', outfile=outfile)

#confluencer(inloc)

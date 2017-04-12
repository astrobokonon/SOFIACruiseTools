# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""

import sys
import getpass
import datetime
import numpy as np
import astropy.table as aptable

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


def reSTer(infile, title, role='Team'):
    """
    Given a MIS file, parse it and print out a summary as well as any
    additional specified AOR details for each leg.

    The formatting is specific to some of the specific (table)
    extensions of reST/Markdown.
    """
    # Where the magic happens
    flight = fpmis.parseMIS(infile)

    h1 = "%s" % (title)
    print underliner(h1)
    print h1
    print underliner(h1)
    print ""
    print "Cheat Sheet generated on %s" % (datetime.datetime.now()),
    print "by %s in %s mode" % (getpass.getuser(), role)
    print ""

    if role == 'Team':
        h2 = "Flight Path"
        print h2
        print underliner(h2)
        print ""
        fpimg = infile[:-4] + ".png"
        print ".. image:: %s" % (fpimg)
        print ""

#    flightnotes = []
#    try:
#        f = open(infile[:-4] + '.rst')
#        flightnotes = f.readlines()
#        f.close()
#    except IOError:
#        pass
#    if flightnotes == []:
#        print "No supplemental notes"
#    else:
#        for com in flightnotes:
#            print com
#    print ""

    h2 = "Flight Metadata"
    print h2
    print underliner(h2)
    print "* Plan Filename: %s, Vintage: %s" %\
        (flight.filename, flight.saved)
    summy = flight.summarize()
    # Break at the line breaks so we can indent it
    #   (ended up taking out the tabs, but keeping this in case we want it)
    summarylines = summy.split("\n")
    for line in summarylines:
        print "* %s" % (line)
    print ""

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
                      str(oach.range_elev),
                      str(oach.range_rof),
                      str(oach.range_rofrt),
                      str(oach.range_thdgrt)]

            obstab.append(tabdat)
    if role == 'Team':
        tabbie = aptable.Table(rows=obstab, names=obstabhed)
        tabbie.write(sys.stdout, format='ascii.rst')
    elif role == 'TO':
        tabbie = aptable.Table(rows=obstab, names=obstabhed)
        tabbie.write(sys.stdout, format='ascii.csv')

    print ""

    print "Flight AOR Catalog"
    print underliner("Flight AOR Catalog")
    print ""

#    OMC AORs
#    aorids = [['88_0005_43', '88_0005_42', '88_0005_41', '88_0005_40',
#           '88_0005_65', '88_0005_64', '88_0005_67', '88_0005_66',
#           '88_0005_61', '88_0005_60', '88_0005_63', '88_0005_62',
#           '88_0005_68', '88_0005_9', '88_0005_55', '88_0005_56',
#           '88_0005_57', '88_0005_38', '88_0005_39', '88_0005_73',
#           '88_0005_32', '88_0005_33', '88_0005_30', '88_0005_31',
#           '88_0005_36', '88_0005_37', '88_0005_34', '88_0005_35',
#           '88_0005_82', '88_0005_81', '88_0005_80', '88_0005_79',
#           '88_0005_69', '88_0005_51', '88_0005_52', '88_0005_53',
#           '88_0005_54', '88_0005_72', '88_0005_70', '88_0005_71']

    aorfiles = ['/Users/rhamilton/Desktop/AORs/04_0026.aor',
                '/Users/rhamilton/Desktop/AORs/90_0083.aor',
                '/Users/rhamilton/Desktop/AORs/04_0119.aor']

    aorids = [
              [],
              ['90_0083_3', '90_0083_17', '90_0083_18', '90_0083_19'],
              []
              ]

    if role == 'Team':
        output = 'rst'
    elif role == 'TO':
        output = 'tab'
    elif role == 'Confluence':
        output = 'confluence'

    for i, each in enumerate(aorfiles):
        aorparse.HAWCAORSorter(each, aorids=aorids[i], output=output)

    # Now go leg-by-leg and print out the gory details.
    if role == 'Team':
        print "Leg Details"
        print underliner("Leg Details")
        print ""
        legnotes = []
        try:
            f = open(infile[:-4] + '.conf')
            flightnotes = f.readlines()
            f.close()
        except IOError:
            pass
        for j, cleg in enumerate(flight.legs):
            pass

    print ""


inloc = '/Users/rhamilton/Research/HAWC/201612/Flights/wx/201612_HA_04_WX12.mis'

reSTer(inloc, 'HAWC+ Comissioning Part 3 and OC4-L', role='Team')
confluencer(inloc)

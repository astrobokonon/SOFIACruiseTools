# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""

import sys
import glob
import numpy as np
import newparse as fpmis
import astropy.table as aptable
import astropy.io.ascii as apascii


def underliner(instr, char="="):
    """
    Given a string, return an "=" underline of the same length.
    """
    slen = len(instr)
    ostr = char * slen
    return ostr


def reSTer(inlist):
    """
    Given a list of filenames, parse each one and print the relevant
    observing leg details (as well as takeoff and landing details).

    The formatting is specific to some of the specific (table)
    extensions of reST/Markdown.
    """
    for i, each in enumerate(inlist):
        # Where the magic happens
        flight = fpmis.parseMIS(each)

        h1 = "FLIGHT %02d" % (i+1)
        print underliner(h1)
        print h1
        print underliner(h1)
        print ""

        h2 = "Flight Path"
        print h2
        print underliner(h2)
        print ""
        fpimg = each[:-4] + ".png"
        print ".. image:: %s" % (fpimg)
        print ""

        print "Top Level Notes"
        print underliner("Top Level Notes")
        print ""
        flightnotes = []
        try:
            f = open(each[:-4] + '.rst')
            flightnotes = f.readlines()
            f.close()
        except IOError:
            pass
        if flightnotes == []:
            print "No supplemental notes"
        else:
            for com in flightnotes:
                print com
        print ""

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

            # print the header before the first leg
            if j == 0:
                obstabhed = ["Leg Number",
                             "Time Since Takeoff at Leg Start (hrs)",
                             "Leg Type", "ObsBlk", "Target",
                             "RA (2000)", "Dec (2000)",
                             "Obs Duration",
                             "Elevation Range",
                             "ROF Range"]

            # Should be self explanatory here
            if oach.legtype == "Takeoff" or oach.legtype == "Landing" or\
               oach.legtype == "Observing":
                tabdat = [oach.legno,
                          np.round(oach.relative_time[0]/60./60., 1),
                          oach.legtype, oach.obsblk,
                          oach.target, oach.ra, oach.dec,
                          str(oach.obsdur),
                          str(oach.range_elev),
                          str(oach.range_rof)]

                obstab.append(tabdat)
        tabbie = aptable.Table(rows=obstab, names=obstabhed)
        tabbie.write(sys.stdout, format='ascii.rst')
        print ""


def confluencer(inlist):
    """
    Given a list of filenames, parse each one and print the relevant
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

    for i, each in enumerate(inlist):
        # Where the magic happens
        flight = fpmis.parseMIS(each)

        print "*FLIGHT %02d*" % (i+1)
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


inloc = '/Users/rhamilton/Research/HAWC/201612/Flights/post-sci-plus/'
inlist = np.array(sorted(glob.glob(inloc + "/*.mis")))

# Cheap hacky way to reorder the flight sequence by hand...won't work if the
#   flight plans aren't sensibly sorted() above, though, so beware.
seq = [0, 1, 2, 4, 3, 5, 6, 7]
inlist = inlist[seq]
#confluencer(inlist)
reSTer(inlist)

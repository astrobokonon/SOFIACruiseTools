# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""

import os
import sys
import glob
import numpy as np
import newparse as fpmis
import astropy.table as aptable


def underliner(instr, char="="):
    """
    Given a string, return an "=" underline of the same length.
    """
    slen = len(instr)
    ostr = char * slen
    return ostr


def sortByDate(inlist):
    """
    Given a random stupid list of named flight plans, return the order that
    provides a date-ordered sequence
    """

    seq = []
    for i, each in enumerate(inlist):
        # Lightly parse each flight (just reads the preamble)
        flight = fpmis.parseMISlightly(each)
        seq.append(flight.takeoff)

    # Sort by takeoff time (flight.takeoff is a datetime obj!)
    newseq = np.argsort(seq)

    return newseq


def reSTer(title, inlist, makeCommentTemplates=False, clobber=False):
    """
    Given a list of filenames, parse each one and print the relevant
    observing leg details (as well as takeoff and landing details).

    The formatting is specific to some of the specific (table)
    extensions of reST/Markdown.
    """

    print title
    print underliner(title, char="#")
    print ""
    print ".. contents:: Table of Contents"
    print "    :depth: 1"
    print "    :backlinks: top"
    print ""

    for i, each in enumerate(inlist):
        # Where the magic happens
        flight = fpmis.parseMIS(each)

        h1 = "FLIGHT %02d" % (i+1)
        print underliner(h1)
        print h1
        print underliner(h1)
        print ""
#
#        h2 = "Flight Path"
#        print h2
#        print underliner(h2)
#        print ""
        fpimg = each[:-4] + ".png"
        print ".. image:: %s" % (fpimg)
        print ""

        h2 = "Flight Information and Summary"
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

        h3 = "Comments"
        print h3
        print underliner(h3)
        print ""
        flightnotes = []

        if makeCommentTemplates is True:
            flightComFile = each[:-3] + 'rst'
            if os.path.exists(flightComFile) is True and clobber is False:
                print "FATAL ERROR: Output %s exists!" % (flightComFile)
                return -1
            else:
                cf = open(flightComFile, 'w')
                cf.write(".. note::\n")
                cf.write("    * General statements\n")
                cf.write("\n")
                cf.write(".. warning::\n")
                cf.write("    * Risky observations or caveats\n")
                cf.write("\n")
                cf.write(".. error::\n")
                cf.write("    * Broken observations/must be changed\n")
                cf.write("\n")
                cf.close()
        else:
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
                    print com.rstrip()
        print ""

    return 0


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

    return 0


seriestitle = 'HAWC+ OC5-E'
inloc = '/Users/rhamilton/Desktop/201705_HA_FirstRealSet/'
inlist = np.array(sorted(glob.glob(inloc + "/*.mis")))

# Cheap hacky way to reorder the flight sequence by hand. Usually better to
#   leave autosort on so they always come out in chronological order, though
seq = [0, 1, 2, 4, 3, 5, 6, 7]
autosort = True
makeCommentTemplates = False
clobber = False
silent = True

if autosort is True:
    newseq = sortByDate(inlist)
else:
    newseq = seq

inlist = inlist[newseq]
#confluencer(inlist)

ret = reSTer(seriestitle, inlist,
             makeCommentTemplates=makeCommentTemplates, clobber=clobber)

if silent is False and ret != -1:
    print "To compile:"
    print "rst2html --link-stylesheet --stylesheet=style2.css",
    print " whatever.rst > whatever.html"

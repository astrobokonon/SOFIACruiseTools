# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""


import glob
import numpy as np
import newparse as fpmis


def confluencer(inlist):
    """
    Given a list of filenames, parse each one and print the relevant
    observing leg details (as well as takeoff and landing details).

    The formatting is specific to Confluence, to insert the results:
        - click on the + icon ("Insert More Content") and choose
          "{ } Markup"
          FOR HAWC+ Confluence (5.9.8 or higher)
            - Choose "Confluence Wiki" as the type, and paste the output
              into the lefthand window; it should then preview nicely on right
          FOR NASA Confluence (5.4.ish)
            - Just paste the output into the box and insert it; it'll preview
              in the main editor window and should be fine
    """

    for i, each in enumerate(inlist):
        flight = fpmis.parseMIS(each)
        print "*FLIGHT %02d*" % (i+1)
        print "\t*Notes:*\n"
        print "\tFlight Plan Filename: %s, Vintage: %s" %\
            (flight.filename, flight.saved)
        summy = flight.summarize()
        # Break at the line breaks so we can indent it
        summarylines = summy.split("\n")
        for line in summarylines:
            print "\t%s" % (line)
        print ""

        for j, oach in enumerate(flight.legs):
            if oach.legtype != "Observing":
                oach.ra = None
                oach.dec = None
                oach.range_rof = [None, None]
                oach.range_elev = [None, None]

            # print the header before the first leg
            if j == 0:
                print "\t||*Leg Number*",
                print "||*Time Since Takeoff at Leg Start (hrs)*",
                print "||*Leg Type*||*Target*||*RA (2000)*||*Dec (2000)*",
                print "||*Obs Duration*||*Elevation Range*||*ROF Range*||"

            # Should be self explanatory here
            if oach.legtype == "Takeoff" or oach.legtype == "Landing" or\
               oach.legtype == "Observing":

                print "\t|%02d|%02.1f|%s|%s|%s|%s|%s|%s, %s|%s, %s|" %\
                    (oach.legno, oach.relative_time[0]/60./60.,
                     oach.legtype, oach.target, oach.ra, oach.dec,
                     oach.obsdur, oach.range_elev[0], oach.range_elev[1],
                     oach.range_rof[0], oach.range_rof[1])
    #        print oach.summarize()
        print "----"


inloc = '/Users/rhamilton/Desktop/Dec2016Flights/Second/'
inlist = np.array(sorted(glob.glob(inloc + "/*.mis")))

# Cheap hacky way to reorder the flight sequence by hand...won't work if the
#   flight plans aren't sensibly sorted() above, though, so beware.
seq = [0, 2, 1, 3, 6, 4, 5, 7]
inlist = inlist[seq]
confluencer(inlist)

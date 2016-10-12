# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 01:14:39 2016

@author: rhamilton
"""

import newparse as fpmis


infile = '/Users/rhamilton/Desktop/201610_FC_01_SCI.mis'

flight = fpmis.parseMIS(infile)
print "Flight Plan Filename: %s, Vintage: %s" % (flight.filename, flight.saved)
print flight.summarize()
print ""
print "-------------------------------------"

for each in flight.legs:
    print each.summarize()
    print ""
    print "-------------------------------------"

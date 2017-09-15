# -*- coding: utf-8 -*-
"""
Created on Fri Aug 30 18:57:54 2013

@author: rhamilton
"""

import numpy as np
import matplotlib.pyplot as plt

import MISparse as fpmis


#infile = '/SalusaSecundus/rhamilton/Research/HAWC/201705/Flights/WXed/02_201705_HA_EAMES_WX12.mis'
infile = '/Users/rhamilton/Research/HAWC/201705/Flights/WXed/02_201705_HA_EAMES_WX12.mis'

# Read the .mis into a helpful class
flight = fpmis.parseMIS(infile, summarize=True)
oleg = flight.legs[6]
print(oleg.summarize())

# Expand the coverage of that flight into something with more points
iflight = fpmis.interp_flight(flight, 2000)

# Interval between LOS rewinds, in degrees of LOS
#   this is the most sensible total range from one end to when the MD starts
#   getting antsy and asking if anyone is going to rewind
los_int = 1.5
los_angle = np.arange(oleg.rof[0], oleg.rof[-1]-los_int, -los_int)

# WARNING WARNING WARNING
# This is just awfully lazy, but np.interp expects monotonically increasing x
#  and we've got decreasing angles on this leg, so just fit it backwards
los_times = np.interp(los_angle[::-1], oleg.rof[::-1], oleg.elapsedtime[::-1])
los_times = los_times[::-1][1:]
# WARNING WARNING WARNING

print("\nObserving interval between LOS rewinds (mins):")
plt.plot(np.array(oleg.elapsedtime)/60., oleg.rof)
i = 0
for each in los_times:
    plt.axhline(los_angle[i], color='grey', linewidth=1, linestyle=':')
    plt.axvline(each/60., color='r', linewidth=1, linestyle=":")
    if i == 0:
        print("%04.2f" % (each/60.))
    else:
        print("%04.2f" % ((each - los_times[i-1])/60.))
    i += 1
plt.show()

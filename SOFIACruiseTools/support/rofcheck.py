# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 15:01:37 2016

@author: rhamilton
"""

import ephem
import datetime


def checkVPAatTime(location, otime, targ):
    # Create an observer at the start location/date/time of SOFIA
    sofia = ephem.Observer()

    # SOFIA mission-type parameters
    airtemp = -50.0     # Decent average flight altitude temperature
    altitude = 12100    # 12100 meters ~= 39700 ft
    horizon = 20        # 20 degrees is lower limit of vignetting

    # Pyephem needs string inputs. Annoying, but whatevs.
    sofia.lat = location[0]
    sofia.lon = location[1]

    sofia.elevation = altitude
    sofia.temp = airtemp
    sofia.date = otime
    sofia.horizon = horizon
    sofia.compute_pressure()
    sofia.name = "eSOFIA"

    targetpos = ephem.FixedBody()
    targetpos._ra = targ[0]
    targetpos._dec = targ[1]
    targetpos._pmra = targ[2]
    targetpos._pmdec = targ[3]
    targetpos.name = targ[4]
    targetpos._epoch = "2000"

    targetpos.compute(sofia)
    print(targetpos._ra, targetpos._dec)
    print(targetpos.alt, targetpos.az)
    return targetpos.parallactic_angle().real * 180./ephem.pi


#============================================================
moons = ((ephem.Io(), 'i'),
         (ephem.Europa(), 'e'),
         (ephem.Ganymede(), 'g'),
         (ephem.Callisto(), 'c'))

# How to place discrete characters on a line that actually represents
# the real numbers -maxradii to +maxradii.

linelen = 65
maxradii = 30.


def put(line, character, radii):
    if abs(radii) > maxradii:
        return
    offset = radii / maxradii * (linelen - 1) / 2
    i = int(linelen / 2 + offset)
    line[i] = character

interval = ephem.hour * 1
now = ephem.now()
now += ephem.hour
now -= now % interval

t = now
while t < now + 2:
    line = [' '] * linelen
    put(line, 'J', 0)
    for moon, character in moons:
        moon.compute(t)
        put(line, character, moon.x)
    print(str(ephem.date(t))[5:], ''.join(line).rstrip())
    t += interval

print('East is to the right;',)
print(', '.join([ '%s = %s' % (c, m.name) for m, c in moons ]))

# =======
otime = datetime.datetime(2016, 12, 1, 7, 59, 20)
targ = ['2:25:40.5999', '62:05:51.590', 0., 0., "W3"]
lat = '28.927002'
lon = '-127.8479'

targvpa = checkVPAatTime([lat, lon], otime, targ)
st = "Target: %s\t\tVPA: %.3lf\tROF: %.3lf" % \
    (targ[4], targvpa, (targvpa + 360.) % 360.)
print(st)
# =======
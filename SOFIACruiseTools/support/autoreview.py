#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 11:37:09 2017

@author: rhamilton
"""

import numpy as np
from .MISparse import flightcomments, commentinator


def autoReview(flight, clear=True):
    """
    Given a parsed flight class, review it checking for:
        - Sun elevation
        - Moon angle
        - Elevation range problems
        - Short legs
        - No setup time
        - Fast rotation
        - Fast heading changes
        - Combination of those last two
    """
    if clear is True:
        comments = flightcomments()
    
    for leg in flight.legs:
#        print("Leg %02i, %s %s" % (leg.legno, leg.legtype, leg.target))
        # We only care about the observing legs
        if leg.legtype == 'Observing':
            basetag = "* Leg %02i: " % (leg.legno)
            
            if np.where(np.array(leg.sunelev) >= -5) != np.array([]):
                comments = commentinator(comments, 'error', basetag,
                                               "Uh, it's daytime")
                                
            if np.where(np.array(leg.elev) <= 23) != np.array([]):
                comments = commentinator(comments, 'warning', basetag,
                                               "Low target elevations")

            elif np.where(np.array(leg.elev) >= 57) != np.array([]):
                comments = commentinator(comments, 'warning', basetag,
                                               "High target elevations")
            
            if leg.obsdur.total_seconds() < 15.*60.:
                # To try to catch the setup leg which has no obs duration
                if leg.obsdur.total_seconds() != 0.:
                    comments = commentinator(comments, 'warning', 
                                                   basetag,
                                                   "Short leg! < 15 minutes.")

            if (leg.duration - leg.obsdur).total_seconds() == 0.:
                comments = commentinator(comments, 'warning', basetag,
                                               "No setup time; expected?")

            if leg.moonangle < 20.:
                comments = commentinator(comments, 'warning', basetag,
                                               "Close moon (< 20 degrees)")
            
            # Need the [1:] because the first ROF rate is always N/A
            if np.where(np.array(leg.rofrt[1:]) < -0.2) != np.array([]):
                if np.where(np.array(leg.rofrt[1:]) < -0.325) != np.array([]):
                    comments = commentinator(comments, 'warning', 
                                                   basetag,
                                                   "Fast negative rotator")
                else:
                    comments = commentinator(comments, 'warning', 
                                                   basetag,
                                                   "Moderate negative rotator")
                            
            if np.where(np.array(leg.rofrt[1:]) > 0.2) != np.array([]):
                if np.where(np.array(leg.rofrt[1:]) > 0.325) != np.array([]):
                    comments = commentinator(comments, 'warning', 
                                                   basetag,
                                                   "Fast positive rotator")
                else:
                    comments = commentinator(comments, 'warning', 
                                                   basetag,
                                                   "Moderate positive rotator")

            # Check up on the heading changes combined with ROF rates
            #   degrees/step; not time units yet
            thr = (np.array(leg.thdg[1:]) - np.array(leg.thdg[:-1]))
            # Elapsed time is time since start of leg; assuming a sensible
            #   linear spacing, just take the 2nd step as the interval
            thr /= leg.elapsedtime[1]/60.
            
            comborate = np.array(leg.rofrt[1:]) + thr
            if np.where(thr >= 0.2) != np.array([]):
                comments = commentinator(comments, 'warning', basetag,
                                               "Fast positive heading changes")

            if np.where(thr <= -0.2) != np.array([]):
                comments = commentinator(comments, 'warning', basetag,
                                               "Fast negative heading changes")

            if np.where(comborate >= 0.325) != np.array([]):
                ntag = "Fast combined positive (ROF + THdg) rotator"
                comments = commentinator(comments, 'warning', 
                                               basetag, ntag)
                
            if np.where(comborate <= -0.325) != np.array([]):
                ntag = "Fast combined negative (ROF + THdg) rotator"
                comments = commentinator(comments, 'warning', 
                                               basetag, ntag)
    
    return comments

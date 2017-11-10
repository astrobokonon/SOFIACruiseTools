#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 15:27:58 2017

@author: rhamilton
"""

import numpy as np


def flightProgramSummarizer(flight):
    """
    Given a flight class, split it into a dict of program IDs that allows
    summarization of targets and times per program.  Because managers.
    """
    # In the given flight, go leg by leg and collect the stuff
    for eachleg in flight.legs:
        print(eachleg.target, eachleg.progid, eachleg.obstime)

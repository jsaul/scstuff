#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (C) GFZ Potsdam                                               #
# All rights reserved.                                                    #
#                                                                         #
# Author: Joachim Saul (saul@gfz-potsdam.de)                              #
#                                                                         #
# GNU Affero General Public License Usage                                 #
# This file may be used under the terms of the GNU Affero                 #
# Public License version 3.0 as published by the Free Software Foundation #
# and appearing in the file LICENSE included in the packaging of this     #
# file. Please review the following information to ensure the GNU Affero  #
# Public License version 3.0 requirements will be met:                    #
# https://www.gnu.org/licenses/agpl-3.0.html.                             #
###########################################################################

import sys
import seiscomp.seismology

# uses the iasp91 tables by default
ttt = seiscomp.seismology.TravelTimeTable()

# iasp91 and ak135 are the only supported models
ttt.setModel("ak135")

def computeTravelTimes(delta, depth):
    arrivals = ttt.compute(0, 0, depth, 0, delta, 0, 0)
    return arrivals

delta = float(sys.argv[1])
depth = float(sys.argv[2])

arrivals = computeTravelTimes(delta, depth)

for arr in arrivals:
    print("%-10s %8.3f %10.6f %10.6f %10.6f" % (arr.phase, arr.time, arr.dtdd, arr.dtdh, arr.dddp))

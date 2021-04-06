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

# Dump moment tensor information to text.
#
# Could be invoked in a pipeline like:
#
#  scstuff.xml-dump-with-mt.py --debug -d "$db" -E "$evid" |
#  scstuff.xml-to-mt-txt.py

import sys, optparse
import scstuff.util
import scstuff.mtutil

description="%prog - dump moment tensor information from XML files to text"

p = optparse.OptionParser(usage="%prog filename[s] >", description=description)
p.add_option("-v", "--verbose", action="store_true", help="run in verbose mode")

(opt, filenames) = p.parse_args()

if not filenames:
    filenames = [ "-" ]

for filename in filenames:
    ep = scstuff.util.readEventParametersFromXML(filename)

    for i in range(ep.focalMechanismCount()):
        fm = ep.focalMechanism(i)
        txt = scstuff.mtutil.fm2txt(fm)
        print(txt)

    del ep

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

"""
Dump moment tensor information to text.

Could be invoked in a pipeline like:

  scstuff-xml-dump-with-mt.py -d "$db" -E "$evid" |
  scstuff-xml-to-mt-txt.py
"""

import sys
import optparse
import scstuff.util
import scstuff.mtutil


def main():

    description="%prog - dump moment tensor information from XML files to text"

    p = optparse.OptionParser(usage="%prog filename[s] >", description=description)
    p.add_option("-E", "--event", help="specify event ID")
    p.add_option("-v", "--verbose", action="store_true", help="run in verbose mode")

    (opt, filenames) = p.parse_args()

    if not filenames:
        filenames = [ "-" ]

    if opt.verbose:
        if opt.event:
            print("output limited to event", opt.event, file=sys.stderr)

    for filename in filenames:
        if opt.verbose:
            print("Working on imput file", filename, file=sys.stderr)

        ep = scstuff.util.readEventParametersFromXML(filename)

        # Create a list of publicID's of the focal mechanisms
        # that we are interested in.
        focalMechanismIDs = []
        for i in range(ep.eventCount()):
            event = ep.event(i)
            # If we explicitly specified an event ID, we skip
            # all other events.
            if opt.event and event.publicID() != opt.event:
                continue
            focalMechanismIDs = event.preferredFocalMechanismID()

        if opt.verbose:
            print(focalMechanismIDs, file=sys.stderr)

        # We are now on the safe side that we only consider focal
        # mechanisms that are the preferred focal mechanisms of any
        # or even only a specific event.

        for i in range(ep.focalMechanismCount()):
            fm = ep.focalMechanism(i)
            if fm.publicID() not in focalMechanismIDs:
                continue
            txt = scstuff.mtutil.fm2txt(fm)
            print(txt)

if __name__ == "__main__":
    main()

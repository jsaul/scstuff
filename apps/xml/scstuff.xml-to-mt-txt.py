#!/usr/bin/env seiscomp-python
#
# Dump moment tensor information to text.
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  python scxml-to-mt-bulletin.py

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

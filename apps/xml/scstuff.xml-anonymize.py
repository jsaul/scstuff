#!/usr/bin/env seiscomp-python
#
# Remove some meta information from creationInfo
#
# Could be invoked in a pipeline like:
#
#  scstuff.xml-dump-with-mt.py -d "$db" -E "$evid" |
#  scstuff.xml-anonymize.py > $evid.xml
#

import sys
import scstuff.util

filenames = sys.argv[1:]
if not filenames:
    filenames = [ "-" ]

for filename in filenames:
    ep = scstuff.util.readEventParametersFromXML(filename)
    scstuff.util.removeAuthorInfo(ep)
    scstuff.util.removeComments(ep)
    scstuff.util.writeEventParametersToXML(ep, filename)
    del ep

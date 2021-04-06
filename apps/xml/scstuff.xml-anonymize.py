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

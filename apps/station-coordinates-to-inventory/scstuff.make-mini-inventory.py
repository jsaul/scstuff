#!/usr/bin/env python
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
import optparse
import scstuff.inventory
import seiscomp.io

description="%prog - create a SeisComP inventory XML from a simple text file"

p = optparse.OptionParser(usage="%prog input >", description=description)
#p.add_option("-v", "--verbose", action="store_true", help="run in verbose mode")

(opt, filenames) = p.parse_args()
assert len(filenames) == 1
filename = filenames[0]

inventory = scstuff.inventory.inventoryFromStationLocationFile(filename)

formatted = True
ar = seiscomp.io.XMLArchive()
ar.setFormattedOutput(formatted)
ar.create("-")
ar.writeObject(inventory)
ar.close()

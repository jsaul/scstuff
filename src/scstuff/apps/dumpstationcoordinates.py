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
This utility
* reads a SeisComP inventory from database
* iterates over the inventory
* dumps network/station code, latitude, longitude, elevation for each station in inventory
* serves as an example on how it can be done in SeisComP/Python using the application class
"""

import sys
import seiscomp.client
import seiscomp.core
from scstuff.inventory import InventoryIterator

class App(seiscomp.client.Application):
    def __init__(self, argc, argv):
        super().__init__(argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()
        lines = []
        coord = {}
        inv = seiscomp.client.Inventory.Instance().inventory()

        for (network, station, location, stream) in InventoryIterator(inv, now):
            n,s,l,c = network.code(), station.code(), location.code(), stream.code()
            if (n,s) in coord:
                continue

            coord[n,s] = (station.latitude(), station.longitude(), station.elevation())

        for (n,s) in coord:
            lat,lon,elev = coord[n,s]
            lines.append("%-2s %-5s %8.4f %9.4f %4.0f" % (n,s,lat,lon,elev))

        lines.sort()
        for line in lines:
            print(line)
        return True


def main():
    app = App(len(sys.argv), sys.argv)
    app()


if __name__ == "__main__":
    main()

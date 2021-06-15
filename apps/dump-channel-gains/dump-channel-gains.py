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
import seiscomp.core
import seiscomp.client
from scstuff.inventory import InventoryIterator

class InvApp(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()
        lines = []
        inv = seiscomp.client.Inventory.Instance().inventory()

        for network, station, location, stream in InventoryIterator(inv, now):
            n,s,l,c = network.code(), station.code(), location.code(), stream.code()
            if l.strip() == "": l="--" # for readability
            line = "%-2s %-5s %-2s %-3s %g" % (n,s,l,c, stream.gain())
            lines.append(line)
        lines.sort()
        for line in lines:
            print(line)
        return True


def main(argc, argv):
    app = InvApp(argc, argv)
    app()


if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv
    main(argc, argv)

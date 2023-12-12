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
import seiscomp.client
import seiscomp.core
import seiscomp.datamodel
from scstuff.inventory import InventoryIterator
from scstuff.util import configuredStreams


class App(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(True)
        self.setLoadConfigModuleEnabled(True)

    def run(self):
        now = seiscomp.core.Time.GMT()

        inv = seiscomp.client.Inventory.Instance().inventory()
        inv_streams = []
        for network, station, location, stream in InventoryIterator(inv, now):
            n, s, l, c = network.code(), station.code(), location.code(), stream.code()
            if l=="":
                l = "--"
            c = c[:2]
            nslc = n, s, l, c
            if nslc not in inv_streams:
                inv_streams.append(nslc)

        cfg_streams = configuredStreams(self.configModule(), self.name())

        lines = []
        for nslc in cfg_streams:
            if nslc not in inv_streams:
                line = "configured stream %-2s %-5s %-2s %-2s not found in inventory" % nslc
                lines.append(line)
        for line in sorted(lines):
            print(line)

        return True


def main(argc, argv):
    app = App(argc, argv)
    app()


if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv
    main(argc, argv)

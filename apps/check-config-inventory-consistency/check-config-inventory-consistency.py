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

    def createCommandLineDescription(self):
        self.commandline().addGroup("Mode")
        self.commandline().addOption("Mode", "inventory,I", "Find items in inventory missing in config")
        self.commandline().addOption("Mode", "config,C",    "Find items in config missing in inventory")
        return True

    def validateParameters(self):
        if not seiscomp.client.Application.validateParameters(self):
            return False
        self.configMode = self.commandline().hasOption("config")
        self.inventoryMode = self.commandline().hasOption("inventory")
        if not self.configMode and not self.inventoryMode:
            self.configMode = self.inventoryMode = True
        return True

    def run(self):
        # perhaps make this configurable
        now = seiscomp.core.Time.GMT()

        inv = seiscomp.client.Inventory.Instance().inventory()
        inv_streams = []
        for network, station, location, stream in InventoryIterator(inv, now):
            n, s, l, c = network.code(), station.code(), location.code(), stream.code()
            if l=="":
                l = "--"
            c = c[:2]
            nslc = n, s, l, c

            # FIXME: Adhoc filter to be made configurable
            # FIXME: We are here only interested in the usual [BMSH]H? channels
            if c[0] not in "BMSH" or c[-1] != "H":
                continue

            if nslc not in inv_streams:
                inv_streams.append(nslc)

        cfg_streams = configuredStreams(self.configModule(), self.name())

        # FIXME:
        # It is usually fine if there are more streams in the inventory than are configured for processing.
        # But we may only want to warn about streams in the inventory that are NOT configured for processing
        # IF there is no other stream for the same NS or NSL configured.
        # In other words: If AB.CDEF.00.BH is configured for processing then it usually doesn't matter that
        # AB.CDEF.00.HH is not configured for processing.

        lines = []
        if self.configMode:
            for nslc in cfg_streams:
                if nslc not in inv_streams:
                    line = "%-2s %-5s %-2s %-2s configured but not found in inventory" % nslc
                    lines.append(line)
        if self.inventoryMode:
            for nslc in inv_streams:
                if nslc not in cfg_streams:
                    line = "%-2s %-5s %-2s %-2s not configured but found in inventory" % nslc
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

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
import seiscomp.logging
from scstuff.inventory import InventoryIterator
import scstuff.util

class App(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setLoggingToStdErr(True)
        self.setLoadInventoryEnabled(False)
# TEMP
#       self.setLoadConfigModuleEnabled(True)
        self._xmlFile = None

    def createCommandLineDescription(self):
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "xml", "specify xml file")

        self.commandline().addGroup("Filter")
        self.commandline().addOption(
            "Filter", "configured-only,C", "only consider configured streams")
        self.commandline().addStringOption(
            "Filter", "time,t", "extract responses valid at the given time")

        self.commandline().addGroup("Output")
        self.commandline().addStringOption(
            "Output", "prefix,o", "path/file prefix of output files")

        return True

    def validateParameters(self):
        if not seiscomp.client.Application.validateParameters(self):
            return False

        try:
            self._xmlFile = self.commandline().optionString("xml")
        except:
            self._xmlFile = None

        if self._xmlFile:
            # With an XML file, we need neither messaging nor database.
            self.setDatabaseEnabled(False, False)
            self.setMessagingEnabled(False)
            self.setLoadInventoryEnabled(False)
        else:
            # Without XML file specified, we fall back to database. And
            # we distinguish between explicitly specified database address
            # and database address obtained from messaging. In other words
            # if the database wasn't specified, we need the messaging.
            if self.commandline().hasOption("database"):
                self.setMessagingEnabled(False)
            else:
                self.setMessagingEnabled(True)
            self.setDatabaseEnabled(True, True)
            self.setLoadInventoryEnabled(True)

        try:
            self._time = self.commandline().optionString("time")
        except:
            self._time = None

        if self._time:
            time = seiscomp.core.Time()
            assert time.fromString(self._time, "%F")
            self._time = time
        else:
            self._time = seiscomp.core.Time.GMT()

        try:
            self._prefix = self.commandline().optionString("prefix")
        except:
            self._prefix = None

        self._configured_only = self.commandline().hasOption("configured-only")

        return True

    def readInventoryFromXML(self):
        ar = seiscomp.io.XMLArchive()
        if ar.open(self._xmlFile) == False:
            raise IOError(self._xmlFile + ": unable to open")
        obj = ar.readObject()
        if obj is None:
            raise TypeError(self._xmlFile + ": invalid format")
        inv  = seiscomp.datamodel.Inventory.Cast(obj)
        if inv is None:
            raise TypeError(self._xmlFile + ": no inventory found")
        return inv

    def getConfiguredStreams(self):
        """
        Retrieve from the config database a list of configured streams.

        Configured here means that these are the streams configured to
        be used in real-time processing.
        """

        if self._xmlFile:
            # TODO: Review: no config in case of XML inventory
            return

        mod = self.configModule()
        items = list()
        for i in range(mod.configStationCount()):
            cfg = mod.configStation(i)
            setup = seiscomp.datamodel.findSetup(cfg, self.name(), True)
            if not setup:
                continue

            params = seiscomp.datamodel.ParameterSet.Find(setup.parameterSetID())
            if not params:
                continue

            detecStream = None
            detecLocid = ""
            for k in range(params.parameterCount()):
                param = params.parameter(k)
                if param.name() == "detecStream":
                    detecStream = param.value()
                elif param.name() == "detecLocid":
                    detecLocid = param.value()
            if detecLocid == "":
                detecLocid = "--"
            if not detecStream:
                continue

            item =  (cfg.networkCode(), cfg.stationCode(), detecLocid, detecStream)
            items.append(item)

        return sorted(items)


    def run(self):
        lines = []
        configured = None

        if self._xmlFile:
            inv = self.readInventoryFromXML()
        else:
            # Access the global inventory instance which is
            # automatically loaded.
            inv = seiscomp.client.Inventory.Instance().inventory()

            if self._configured_only:
                configured = self.getConfiguredStreams()
    
        seiscomp.logging.debug("time is "+(self._time.toString("%FT%TZ")))

        for network, station, location, stream in InventoryIterator(inv, self._time):
            net = network.code()
            sta = station.code()
            loc = location.code()
            cha = stream.code()

            if configured and (net, sta, loc, cha[:2]) not in configured:
                continue

            item = "%s.%s.%s.%s" % (net,sta,loc,cha)
            s = scstuff.util.sacpz(network, station, location, stream)
            if not s:
                continue
            filename = self._prefix+item+".sacpz"
            seiscomp.logging.debug("writing "+filename)
            with open(filename, "w") as f:
                f.write(s)

        return True


def main(argc, argv):
    app = App(argc, argv)
    app()


if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv
    main(argc, argv)

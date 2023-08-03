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
import seiscomp.datamodel
import seiscomp.io
import seiscomp.logging
import scstuff.dbutil


def parse_time_string(s):
    t = seiscomp.core.Time.GMT()
    for fmt in [ "%FT%T.%fZ", "%FT%TZ", "%F %T" ]:
        if t.fromString(s, fmt):
            return t
    print("Wrong time format", file=sys.stderr)


class PickLoader(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)
        self.setLoadConfigModuleEnabled(True)
        self._startTime = self._endTime = None
        # time window relative to origin time of specified event:
        self._before = 4*3600. # 4 hours
        self._after  = 1*3600. # 1 hour

    ###########################################################################
    def initConfiguration(self):
        if not seiscomp.client.Application.initConfiguration(self):
            return False

        # If the database connection is passed via command line or configuration
        # file then messaging is disabled. Messaging is only used to get
        # the configured database connection URI.
        seiscomp.logging.warning(self.databaseURI())
        if self.databaseURI() != '':
            self.setMessagingEnabled(False)
        else:
            # A database connection is not required if the inventory is loaded
            # from file
            if not self.isInventoryDatabaseEnabled():
                self.setMessagingEnabled(False)
                self.setDatabaseEnabled(False, False)

        return True

    def createCommandLineDescription(self):
        seiscomp.client.Application.createCommandLineDescription(self)
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "begin", "specify start of time window")
        self.commandline().addStringOption("Dump", "end", "specify end of time window")
        self.commandline().addStringOption("Dump", "event", "compute a time window from the event")
        self.commandline().addStringOption("Dump", "before", "start time window this many seconds before origin time")
        self.commandline().addStringOption("Dump", "after",  "end time window this many seconds after origin time")
        self.commandline().addStringOption("Dump", "origins",
            "specify space separated list of origin ids to be also loaded")
        self.commandline().addStringOption("Dump", "network-blacklist",
            "specify space separated list of network codes to be excluded")
        self.commandline().addStringOption("Dump", "author-whitelist",
            "specify space separated list of author IDs to be included. If not given, no author filtering is applied")
        self.commandline().addOption("Dump", "no-origins", "don't include any origins")
        self.commandline().addOption("Dump", "no-manual-picks", "don't include any manual picks")

    def _processCommandLineOptions(self):
        try:    start = self.commandline().optionString("begin")
        except: start = None

        try:    end = self.commandline().optionString("end")
        except: end = None

        try:
            orids = self.commandline().optionString("origins")
            self._orids = orids.split()
        except:
            self._orids = []

        try:
            self._evid = self.commandline().optionString("event")
        except:
            self._evid = ""

        # only if we got an event ID we need to look for "--before" and "--after"
        if self._evid:
            if self.commandline().hasOption("before"):
                before = self.commandline().optionString("before")
                self._before = float(before)
            if self.commandline().hasOption("after"):
                after  = self.commandline().optionString("after")
                self._after = float(after)

        if start:
            self._startTime = parse_time_string(start)
            if not self._startTime:
                return False
        if end:
            self._endTime = parse_time_string(end)
            if not self._endTime:
                return False
        try:
            self._networkBlacklist = self.commandline().optionString("network-blacklist").split()
        except:
            self._networkBlacklist = []

        try:
            self._authorWhitelist = self.commandline().optionString("author-whitelist").split()
        except:
            self._authorWhitelist = None

        return True

    def run(self):
        if not self._processCommandLineOptions():
            return False

        dbq = self.query()
        ep  = seiscomp.datamodel.EventParameters()

        # If we got an event ID as command-line argument...
        if self._evid:
            # Retrieve event from DB
            evt = dbq.loadObject(seiscomp.datamodel.Event.TypeInfo(), self._evid)
            evt = seiscomp.datamodel.Event.Cast(evt)
            if evt is None:
                raise TypeError("unknown event '" + self._evid + "'")
            # If start time was not specified, compute it from origin time.
            if self._startTime is None:
                orid = evt.preferredOriginID()
                org = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                org = seiscomp.datamodel.Origin.Cast(org)
                t0 = org.time().value()
                self._startTime = t0 + seiscomp.core.TimeSpan(-self._before)
                self._endTime   = t0 + seiscomp.core.TimeSpan( self._after)

            if not self.commandline().hasOption("no-origins"):
                # Loop over all origins of the event
                for org in dbq.getOrigins(self._evid):
                    org = seiscomp.datamodel.Origin.Cast(org)
                    # We only look for manual events.
                    if org.evaluationMode() != seiscomp.datamodel.MANUAL:
                        continue
                    self._orids.append(org.publicID())

        seiscomp.logging.debug("querying database")
        objects = scstuff.dbutil.loadPicksForTimespan(
                dbq,
                self._startTime, self._endTime,
                withAmplitudes=True, authors=self._authorWhitelist)

        seiscomp.logging.debug("adding %d objects to EventParameters " % len(objects))
        for publicID in objects:
            ep.add(objects[publicID])
        seiscomp.logging.debug("deleting %d objects" % len(objects))
        del objects
        seiscomp.logging.debug("finished deleting objects")

        if not self.commandline().hasOption("no-origins"):
            for i,orid in enumerate(self._orids):
                # XXX There was occasionally a problem with:
                #   org = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                #   org = seiscomp.datamodel.Origin.Cast(org)
                # NOTE when org was directly overwritten.
                # resulting in a segfault. The reason is not clear, but
                # is most probably in the Python wrapper. The the segfault
                # can be avoided by creating an intermediate object 'obj'.
                obj = dbq.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
                org = seiscomp.datamodel.Origin.Cast(obj)
                ep.add(org)
            seiscomp.logging.debug("loaded %d manual origins" % ep.originCount())

        seiscomp.logging.debug("dumping EventParameters to XMLArchive")
        # finally dump event parameters as formatted XML archive to stdout
        ar = seiscomp.io.XMLArchive()
        ar.setFormattedOutput(True)
        ar.create("-")
        ar.writeObject(ep)
        ar.close()
        seiscomp.logging.debug("deleting EventParameters")
        del ep
        seiscomp.logging.debug("done")
        return True


def main():
    app = PickLoader(len(sys.argv), sys.argv)
    app()

if __name__ == "__main__":
    main()

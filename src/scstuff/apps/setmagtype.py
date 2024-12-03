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
A utility to fix the magnitude type by sending a journal message.

Example:

    scstuff-set-magtype --event gfz2019abcd --magnitude-type Mw

to set the magnitude type of event gfz2019abcd to "Mw".
"""


import sys
import socket
import seiscomp.core
import seiscomp.datamodel
import seiscomp.client
import seiscomp.logging


class App(seiscomp.client.Application):

    def __init__(self, argc, argv):
        super().__init__(argc, argv)
        self.setDatabaseEnabled(False, False)
        self.setMessagingEnabled(True)

    def createCommandLineDescription(self):
        self.commandline().addGroup("Config")
        self.commandline().addStringOption("Config", "author", "Set the author name")
        self.commandline().addStringOption("Config", "time",   "Set the publication time")
        self.commandline().addGroup("Event")
        self.commandline().addStringOption("Event", "event,E", "specify event publicID")
        self.commandline().addGroup("Magnitude")
        self.commandline().addStringOption("Magnitude", "magnitude-type,Y", "type of magnitude to set preferred")
        return super().createCommandLineDescription()

    def validateParameters(self):
        if not super().validateParameters():
            return False

        try:
            self._eventID = self.commandline().optionString("event")
        except RuntimeError:
            seiscomp.logging.error("Missing command line parameter '--event'")
            return False

        try:
            self._magType = self.commandline().optionString("magnitude-type")
        except RuntimeError:
            self._magType = None

        return True

    def sendEventJournal(self, eventID, action, params):
        time = seiscomp.core.Time.GMT()
        # override system time if specified on the command line
        try:
            tstr = self.commandline().optionString("time")
        except RuntimeError:
            tstr = None
        if tstr and not time.fromString(tstr, "%FT%T.%fZ"):
            err = "failed to parse time string '%s'" % tstr
            seiscomp.logging.error(err)
            return False

        try:
            author = self.commandline().optionString("author")
        except RuntimeError:
            # author = self.author()
            author = self.name() + "@" + socket.gethostname()

        j = seiscomp.datamodel.JournalEntry()
        j.setObjectID(eventID)
        j.setAction(action)
        j.setParameters(params)
        j.setSender(author)
        j.setCreated(time)
        n = seiscomp.datamodel.Notifier("Journaling", seiscomp.datamodel.OP_ADD, j)
        nm = seiscomp.datamodel.NotifierMessage()
        nm.attach(n)
        if not self.connection().send("EVENT", nm):
            return False
        return True

    def fixMw(self, eventID):
        return self.fixMagnitudeType(eventID, "Mw")

    def releaseMw(self, eventID):
        return self.sendEventJournal(eventID, "EvPrefMw", "false")

    def fixMagnitudeType(self, eventID, magtype, release=False):
        if magtype:
            seiscomp.logging.debug("Fixing magnitude type to " + magtype + " for event " + eventID)

        if magtype == "Mw":
            return self.sendEventJournal(eventID, "EvPrefMw", "true")

        return self.sendEventJournal(eventID, "EvPrefMagType", magtype)

    def releaseMagnitudeType(self, eventID):
        return self.sendEventJournal(eventID, "EvPrefMagType", "")

    def run(self):
        if self._magType is not None:
            if self._magType == "Mw":
                return self.fixMw(self._eventID)

            if self._magType[0].upper() == "M":
                return self.fixMagnitudeType(self._magType)

            raise ValueError("Don't know what to do with magnitude %s" % self._magType)

        return True


def main():
    app = App(len(sys.argv), sys.argv)
    app()


if __name__ == "__main__":
    main()

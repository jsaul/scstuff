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
Example:
    $ scstuff-dump-event-comments --start-time 2024-01-01T00:00:00Z --end-time 2025-01-01T00:00:00Z | grep -v published
    gfz2024aaoe Challenging/emergent onsets at many stations
    gfz2024bfld Very nice pP
    gfz2024dbjy near Vogelsberger Basaltwerk
    gfz2024epoa Karsdorf
    gfz2024gltf Very nice depth phases both pP and sP
    gfz2024hkrb Very nice pP depth phases
    gfz2024hopa Textbook example depth phases
"""

import sys
import seiscomp.client
import seiscomp.core
import seiscomp.datamodel
import scstuff.util

def loadEvent(query, evid):
    """
    Retrieve event from DB incl. children

    Returns either the event instance
    or None if event could not be loaded.

    Uses loadObject() to also load the children.
    """
    event = query.loadObject(seiscomp.datamodel.Event.TypeInfo(), evid)
    event = seiscomp.datamodel.Event.Cast(event)
    if event:
        if event.eventDescriptionCount() == 0:
            query.loadEventDescriptions(event)
    return event


class App(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoggingToStdErr(True)
        self.setLoadConfigModuleEnabled(True)

        self._xmlEnabled = False

        self._xmlFile = None
        self._eventID = None

        self._startTime = None
        self._endTime = None

    def setXmlFile(self, filename):
        """ To be called from __init__() """
        self._xmlFile = filename
        self.setXmlEnabled(True)

    def xmlEnabled(self):
        return self._xmlEnabled

    def setEventID(self, eventID):
        self._eventID = eventID

    def createCommandLineDescription(self):
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "event,E", "ID of event to dump")

        self.commandline().addStringOption("Input", "start-time", "specify start time")
        self.commandline().addStringOption("Input", "end-time", "specify end time")

        if self.xmlEnabled():
            self.commandline().addStringOption("Input", "xml", "specify xml file")
        return True


    def validateParameters(self):
        # This is where BOTH
        #   (1) the command line arguments are accessible
        #   (2) the set...Enabled methods have an effect
        # Thus e.g. enabling/disabling the database MUST take place HERE.
        # NEITHER in __init__(), where command line arguments are not yet accessible
        # NOR in init() where the database has been configured and set up already.
        if not seiscomp.client.Application.validateParameters(self):
            return False

        try:
            if self.xmlEnabled():
                self._xmlFile = self.commandline().optionString("xml")
        except:
            self._xmlFile = None

        try:
            self._eventID = self.commandline().optionString("event")
        except:
            self._eventID = None

        if self._xmlFile:
            self.setDatabaseEnabled(False, False)
        else:
            self.setDatabaseEnabled(True, True)

        self._startTime = self.commandline().optionString("start-time")
        self._endTime = self.commandline().optionString("end-time")

        self._startTime = scstuff.util.parseTime(self._startTime)
        self._endTime   = scstuff.util.parseTime(self._endTime)

        return True

    def _loadEvent(self, publicID):
        # load an Event object from database
        tp = seiscomp.datamodel.Event
        obj = self.query().loadObject(tp.TypeInfo(), publicID)
        obj = tp.Cast(obj)
        if obj is None:
            seiscomp.logging.error("unknown Event '%s'" % publicID)
        return obj

    def run(self):
        if self._eventID:
            event = self._loadEvent(self._eventID)
            for i in range(event.commentCount()):
                comment = event.comment(i)
                print(self._eventID, comment.text())
                print(dir(comment))
            return True

        if self._startTime  is not None and self._endTime is not None:
            tp = seiscomp.datamodel.Event
            events = list()
            for obj in self.query().getEvents(self._startTime, self._endTime):
                event = tp.Cast(obj)
                if event is None:
                    continue
                events.append(event)
            for event in events:
                self.query().loadComments(event)
                for i in range(event.commentCount()):
                    comment = event.comment(i)
                    print(event.publicID(), comment.text())

        return True


def main():
    app = App(len(sys.argv), sys.argv)
    app()
    return 0


if __name__ == "__main__":
    main()

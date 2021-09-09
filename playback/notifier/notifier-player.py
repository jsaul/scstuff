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

import sys, os
import seiscomp.core
import seiscomp.client
import seiscomp.datamodel
import seiscomp.io
import seiscomp.logging
import seiscomp.utils


def notifierMessageFromXML(xml):
    b = seiscomp.utils.stringToStreambuf(xml)
    ar = seiscomp.io.XMLArchive(b)
    obj = ar.readObject()
    if obj is None:
        raise TypeError("got invalid xml")
    nmsg = seiscomp.datamodel.NotifierMessage.Cast(obj)
    if nmsg is None:
        raise TypeError("no NotifierMessage object found")
    return nmsg

def notifierInput(filename):
    f = open(filename)
    while True:
        while True:
            line = f.readline()
            if not line:
                # empty input
                return True
            line = line.strip()
            if not line:
                # blank line
                continue
            if line[0] == "#":
                break

        if len(line.split()) == 3:
            sharp, timestamp, nbytes = line.split()
        elif len(line.split()) == 4:
            sharp, timestamp, nbytes, sbytes = line.split()
            assert sbytes == "bytes"
        elif len(line.split()) == 5:
            sharp, timestamp, md5hash, nbytes, sbytes = line.split()
            assert sbytes == "bytes"
        else:
            break

        assert sharp[0] == "#"
        time = seiscomp.core.Time.GMT()
        time.fromString(timestamp, "%FT%T.%fZ")

        nbytes = int(nbytes)
        assert sharp[0] == "#"
        xml = f.read(nbytes).strip()

        yield time, notifierMessageFromXML(xml)


class NotifierPlayer(seiscomp.client.Application):

    def __init__(self, argc, argv):
        super(NotifierPlayer, self).__init__(argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self._startTime = self._endTime = None
        self.xmlInputFileName = None
        self._time = None

    def createCommandLineDescription(self):
        super(NotifierPlayer, self).createCommandLineDescription()
        self.commandline().addGroup("Play")
        self.commandline().addStringOption("Play", "begin", "specify start of time window")
        self.commandline().addStringOption("Play", "end", "specify end of time window")
        self.commandline().addGroup("Input")
        self.commandline().addStringOption("Input", "xml-file", "specify xml file")

    def init(self):
        if not super(NotifierPlayer, self).init():
            return False

        try:    start = self.commandline().optionString("begin")
        except: start = None

        try:    end = self.commandline().optionString("end")
        except: end = None

        try:    self.xmlInputFileName = self.commandline().optionString("xml-file")
        except: pass

        if start:
            self._startTime = seiscomp.core.Time.GMT()
            if self._startTime.fromString(start, "%FT%TZ") == False:
                seiscomp.logging.error("Wrong 'begin' format")
                return False
        if end:
            self._endTime = Core.Time.GMT()
            if self._endTime.fromString(end, "%FT%TZ") == False:
                seiscomp.logging.error("Wrong 'end' format")
                return False
        return True

    def run(self):
        if not self.xmlInputFileName:
            return False

        seiscomp.logging.debug("input file is %s" % self.xmlInputFileName)

        for time,nmsg in notifierInput(self.xmlInputFileName):

            if self._startTime is not None and time < self._startTime:
                continue
            if self._endTime is not None and time > self._endTime:
                break
            self.sync(time)

            # We either extract and handle all Notifier objects individually
            for item in nmsg:
                n = seiscomp.datamodel.Notifier.Cast(item)
                assert n is not None
                n.apply()
                self.handleNotifier(n)
            # OR simply handle the NotifierMessage
#           self.handleMessage(nmsg)

        return True

    def sync(self, time):
        self._time = time
        seiscomp.logging.debug("sync time=%s" % time.toString("%FT%T.%fZ"))

    def addObject(self, parent, obj):
        # in a usable player, this must be reimplemented
        seiscomp.logging.debug("addObject class=%s parent=%s" % (obj.className(),parent))

    def updateObject(self, parent, obj):
        # in a usable player, this must be reimplemented
        seiscomp.logging.debug("updateObject class=%s parent=%s" % (obj.className(),parent))

app = NotifierPlayer(len(sys.argv), sys.argv)
sys.exit(app())

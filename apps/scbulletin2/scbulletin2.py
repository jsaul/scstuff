#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-
############################################################################
# Copyright (C) GFZ Potsdam                                                #
# All rights reserved.                                                     #
#                                                                          #
# GNU Affero General Public License Usage                                  #
# This file may be used under the terms of the GNU Affero                  #
# Public License version 3.0 as published by the Free Software Foundation  #
# and appearing in the file LICENSE included in the packaging of this      #
# file. Please review the following information to ensure the GNU Affero   #
# Public License version 3.0 requirements will be met:                     #
# https://www.gnu.org/licenses/agpl-3.0.html.                              #
############################################################################

import sys
import seiscomp.client
import scstuff.bulletin
import scstuff.dbutil


def usage(exitcode=0):
    usagetext = """
 scbulletin2.py [ -E event-id | -O origin-os] [--input xml-file | -d database ]
    """
    sys.stderr.write("%s\n" % usagetext)
    sys.exit(exitcode)


class BulletinApp(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
#       self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setDaemonEnabled(False)
        self.setLoggingToStdErr(True)
        self.setLoadRegionsEnabled(True)
        self.format = "autoloc3"

    def createCommandLineDescription(self):
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption(
            "Dump", "event,E", "ID of event to dump")
        self.commandline().addStringOption(
            "Dump", "origin,O", "ID of origin to dump")
        self.commandline().addStringOption(
            "Dump", "weight,w",
            "weight threshold for printed and counted picks")
        self.commandline().addOption(
            "Dump", "extra,x", "extra detailed autoloc3 format")
        self.commandline().addOption(
            "Dump", "enhanced,e",
            "enhanced output precision for local earthquakes")
        self.commandline().addOption(
            "Dump", "polarities,p", "dump onset polarities")
        self.commandline().addOption(
            "Dump", "first-only",
            "dump only the first event/origin")
        self.commandline().addOption(
            "Dump", "event-agency-id",
            "use agency ID information from event instead of preferred origin")
        self.commandline().addOption(
            "Dump", "dist-in-km,k",
            "plot distances in km instead of degree")

        self.commandline().addGroup("Input")
        self.commandline().addStringOption(
            "Input", "format,f",
            "input format to use (xml [default], zxml (zipped xml), binary)")
        self.commandline().addStringOption(
            "Input", "input,i", "input file, default: stdin")

        return True

    def validateParameters(self):
        if seiscomp.client.Application.validateParameters(self) is False:
            return False

        if self.commandline().hasOption("input"):
            self.setDatabaseEnabled(False, False)
            self.setMessagingEnabled(False)
        else:
            self.setDatabaseEnabled(True, True)
            if self.commandline().hasOption("database"):
                self.setMessagingEnabled(False)
            else:
                self.setMessagingEnabled(True)

        return True

    def run(self):

        try:
            eventID = self.commandline().optionString("event")
        except RuntimeError:
            eventID = None

        try:
            originID = self.commandline().optionString("origin")
        except RuntimeError:
            originID = None

        if self.commandline().hasOption("input") \
                or self.commandline().hasOption("format"):
            dbq = None
        else:
            dbq = self.query()
            if dbq is None:
                print("Error: must specify either database or input file")
                return False

        bulletin = scstuff.bulletin.Bulletin()
        bulletin.format = "autoloc3"

        try:
            mw = self.commandline().optionString("weight")
        except RuntimeError:
            mw = None

        if mw != "" and mw is not None:
            bulletin.minArrivalWeight = float(mw)

        if self.commandline().hasOption("extra"):
            bulletin.format = "autoloc3extra"
        else:
            bulletin.format = "autoloc3"

        if self.commandline().hasOption("enhanced"):
            bulletin.enhanced = True

        if self.commandline().hasOption("polarities"):
            bulletin.polarities = True

        if self.commandline().hasOption("event-agency-id"):
            bulletin.useEventAgencyID = True

        if self.commandline().hasOption("dist-in-km"):
            bulletin.distInKM = True

        if dbq:
            ep = scstuff.dbutil.loadCompleteEvent(
                dbq, eventID, comments=True, allmagnitudes=True,
                withPicks=True, preferred=True)
            bulletin.setEventParameters(ep)

            if eventID:
                txt = bulletin.printEvent(eventID)
            elif originID:
                txt = bulletin.printOrigin(originID)
        else:
            # if there is no file name specified
            inputFormat = "xml"

            try:
                inputFile = self.commandline().optionString("input")
            except RuntimeError:
                inputFile = "-"

            if inputFile.lower().endswith(".xml.gz"):
                inputFormat == "gzxml"

            try:
                inputFormat = self.commandline().optionString("format")
            except RuntimeError:
                pass

            if inputFormat in ("xml", "zxml", "gzxml"):
                ar = seiscomp.io.XMLArchive()
                if inputFormat in ("zxml", "gzxml"):
                    ar.setCompression(True)
                    if inputFormat == "gzxml":
                        ar.setCompressionMethod(seiscomp.io.XMLArchive.GZIP)
            elif inputFormat == "binary":
                ar = seiscomp.io.BinaryArchive()
            else:
                raise TypeError("unknown input format '" + inputFormat + "'")

            if ar.open(inputFile) is False:
                raise IOError(inputFile + ": unable to open")

            obj = ar.readObject()
            if obj is None:
                raise TypeError(inputFile + ": invalid format")

            ep = seiscomp.datamodel.EventParameters.Cast(obj)
            if ep is None:
                raise TypeError(inputFile + ": no eventparameters found")

            bulletin.setEventParameters(ep)

            if ep.eventCount() == 0:
                if ep.originCount() == 0:
                    raise TypeError(
                        inputFile + ": "
                        "no origin and no event in eventparameters found")
                else:
                    if self.commandline().hasOption("first-only"):
                        org = ep.origin(0)
                        txt = bulletin.printOrigin(org.publicID())
                    else:
                        txt = ""
                        for i in range(ep.originCount()):
                            org = ep.origin(i)
                            txt += bulletin.printOrigin(org.publicID())
            else:
                if self.commandline().hasOption("first-only"):
                    evt = ep.event(0)
                    if evt is None:
                        raise TypeError(inputFile + ": invalid event")

                    txt = bulletin.printEvent(evt.publicID())
                else:
                    txt = ""
                    for i in range(ep.eventCount()):
                        evt = ep.event(i)
                        txt += bulletin.printEvent(evt.publicID())

        if txt:
            print(txt)

        return True


def main():
    app = BulletinApp(len(sys.argv), sys.argv)
    return app()


if __name__ == "__main__":
    main()

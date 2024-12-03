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
Dump origin, magnitude and moment tensor information for an
event to SeisComP XML.

Could be invoked in a pipeline like:

  python scstuff.xml-dump-with-mt.py --debug -d "$db" -E "$evid" |
  sccnv -f -i trunk:- -o qml1.2:"$evid-mt.QuakeML"

The above will dump the event information to QuakeML 1.2
"""

import sys
import seiscomp.client
import seiscomp.datamodel
import seiscomp.io
import scstuff.dbutil
import scstuff.util


class App(seiscomp.client.Application):

    def __init__(self, argc, argv):
        super().__init__(argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)

    def createCommandLineDescription(self):
        super().createCommandLineDescription()
        self.commandline().addGroup("Dump")
        self.commandline().addStringOption("Dump", "event,E", "specify event id")
        self.commandline().addOption("Dump", "include-full-creation-info,I", "include full creation info")
        self.commandline().addOption("Dump", "all-magnitudes,m", "include network magnitudes of all available types, not only the preferred magnitude")
        self.commandline().addOption("Dump", "comments,c", "include comments")

    def run(self):
        comments = self.commandline().hasOption("comments")

        ep = seiscomp.datamodel.EventParameters()
        evids = self.commandline().optionString("event").split()
        for evid in evids:
            # Each of the specified events is added to the
            # EventParameters instance
            self.do_one_event(evid, ep, comments=comments)

        # Dump formatted XML archive to stdout
        scstuff.util.writeEventParametersToXML(ep)
        return True

    def do_one_event(self, evid, ep, comments=True):
        """
        Things to do:
        * load event
        * load preferred origin without arrivals
        * load at least the preferred magnitude if available, all magnitudes if requested
        * load focal mechanism incl. moment tensor depending on availability, incl. Mw from derived origin
        """

        query = self.query()

        # Load event and preferred origin. This is the minimum
        # required info and if it can't be loaded, give up.
        event = scstuff.dbutil.loadEvent(query, evid, full=True)
        if event is None:
            raise ValueError("unknown event '" + evid + "'")
        preferredOrigin = scstuff.dbutil.loadOrigin(query, event.preferredOriginID(), full=False)
        if preferredOrigin is None:
            raise ValueError("unknown origin '" + event.preferredOriginID() + "'")

        # take care of origin references and leave just one for the preferred origin
        while (event.originReferenceCount() > 0):
            event.removeOriginReference(0)
        if preferredOrigin:
            event.add(seiscomp.datamodel.OriginReference(preferredOrigin.publicID()))
        if comments:
            query.loadComments(preferredOrigin)

        # load all magnitudes for preferredOrigin
        if self.commandline().hasOption("all-magnitudes"):
            query.loadMagnitudes(preferredOrigin)
            magnitudes = [ preferredOrigin.magnitude(i) for i in range(preferredOrigin.magnitudeCount()) ]
        else:
            magnitudes = []

        if event.preferredMagnitudeID():
            for mag in magnitudes:
                if mag.publicID() == event.preferredMagnitudeID():
                    preferredMagnitude = mag
                    break
            else:
                preferredMagnitude = scstuff.dbutil.loadMagnitude(query, event.preferredMagnitudeID(), full=False)
        else:
            preferredMagnitude = None

        # load focal mechanism, moment tensor, moment magnitude and related origins
        momentTensor = momentMagnitude = derivedOrigin = triggeringOrigin = None
        focalMechanism = scstuff.dbutil.loadFocalMechanism(query, event.preferredFocalMechanismID(), full=False)
        if focalMechanism:
            query.loadMomentTensors(focalMechanism)

            for i in range(focalMechanism.momentTensorCount()):
                momentTensor = focalMechanism.momentTensor(i)
                scstuff.util.stripMomentTensor(momentTensor)

            if focalMechanism.triggeringOriginID():
                if event.preferredOriginID() == focalMechanism.triggeringOriginID():
                    triggeringOrigin = preferredOrigin
                else:
                    triggeringOrigin = scstuff.dbutil.loadOrigin(query, focalMechanism.triggeringOriginID(), full=False)

            if focalMechanism.momentTensorCount() > 0:
                momentTensor = focalMechanism.momentTensor(0)  ## FIXME What if there is more than one MT?
                if momentTensor.derivedOriginID():
                    derivedOrigin = scstuff.dbutil.loadOrigin(query, momentTensor.derivedOriginID(), full=False)
                if momentTensor.momentMagnitudeID():
                    if momentTensor.momentMagnitudeID() == event.preferredMagnitudeID():
                        momentMagnitude = preferredMagnitude
                    else:
                        momentMagnitude = scstuff.dbutil.loadMagnitude(query, momentTensor.momentMagnitudeID(), full=False)
            # take care of FocalMechanism and related references
            if derivedOrigin:
                event.add(seiscomp.datamodel.OriginReference(derivedOrigin.publicID()))
            if triggeringOrigin:
                if event.preferredOriginID() != triggeringOrigin.publicID():
                    event.add(seiscomp.datamodel.OriginReference(triggeringOrigin.publicID()))
            while (event.focalMechanismReferenceCount() > 0):
                event.removeFocalMechanismReference(0)
            if focalMechanism:
                event.add(seiscomp.datamodel.FocalMechanismReference(focalMechanism.publicID()))


        # populate EventParameters instance
        ep.add(event)
        if preferredMagnitude and preferredMagnitude is not momentMagnitude:
            preferredOrigin.add(preferredMagnitude)
        ep.add(preferredOrigin)
        if focalMechanism:
            if triggeringOrigin:
                if triggeringOrigin is not preferredOrigin:
                    ep.add(triggeringOrigin)
            if derivedOrigin:
                if momentMagnitude:
                    derivedOrigin.add(momentMagnitude)
                ep.add(derivedOrigin)
            ep.add(focalMechanism)

        if not comments:
            scstuff.util.recursivelyRemoveComments(ep)
        if not self.commandline().hasOption("include-full-creation-info"):
            scstuff.util.recursivelyRemoveAuthor(ep)


def main():
    app = App(len(sys.argv), sys.argv)
    app()


if __name__ == "__main__":
    main()

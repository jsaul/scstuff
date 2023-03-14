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
import seiscomp.client, seiscomp.io, seiscomp.math
import seiscomp.datamodel, seiscomp.logging, seiscomp.seismology


def time2str(time):
    """
    Convert a seiscomp.core.Time to a string
    """
    return time.toString("%Y-%m-%d %H:%M:%S.%f000000")[:23]


def lat2str(lat, enhanced=False):
    if enhanced:
        s = "%.5f " % abs(lat)
    else:
        s = "%.2f " % abs(lat)
    if lat >= 0:
        s += "N"
    else:
        s += "S"
    return s


def lon2str(lon, enhanced=False):
    if enhanced:
        s = "%.5f " % abs(lon)
    else:
        s = "%.2f " % abs(lon)
    if lon >= 0:
        s += "E"
    else:
        s += "W"
    return s


def stationCount(org, minArrivalWeight):
    count = 0
    for i in range(org.arrivalCount()):
        arr = org.arrival(i)
        #   if arr.weight()> 0.5:
        if arr.weight() >= minArrivalWeight:
            count += 1
    return count


def uncertainty(quantity):
    # for convenience/readability: get uncertainty from a quantity
    try:
        err = 0.5*(quantity.lowerUncertainty()+quantity.upperUncertainty())
    except:
        try:
            err = quantity.uncertainty()
        except:
            err = None

    return err


def sortedArrivals(origin):
    arrivals = [ origin.arrival(i) for i in range(origin.arrivalCount()) ]
    return sorted(arrivals, key=lambda t: t.distance())

def picksForOrigin(origin, ep):
    pickIDs = []
    for i in range(origin.arrivalCount()):
        pickIDs.append(origin.arrival(i).pickID())
    picks = {}
    for i in range(ep.pickCount()):
        pick = ep.pick(i)
        if pick.publicID() in pickIDs:
            key = pick.publicID()
            picks[key] = pick
    return picks

def amplitudesForOrigin(origin, ep):
    pickIDs = []
    for i in range(origin.arrivalCount()):
        pickIDs.append(origin.arrival(i).pickID())
    amplitudes = {}
    for i in range(ep.amplitudeCount()):
        amplitude = ep.amplitude(i)
        if amplitude.pickID() in pickIDs:
            key = amplitude.publicID()
            amplitudes[key] = amplitude
    return amplitudes


def eventForOrigin(originID, ep):
    for i in range(ep.eventCount()):
        if ep.event(i).publicID() == originID:
            return ep.event(i)


class Bulletin(object):

    def __init__(self):
        self._ep = None
        self._long = True
        self._evt = None
        self.format = "autoloc3"
        self.enhanced = False
        self.polarities = False
        self.useEventAgencyID = False
        self.distInKM = False
        self.minDepthPhaseCount = 3
        self.minArrivalWeight = 0.5
        self.minStationMagnitudeWeight = 0.5

    def setEventParameters(self, ep):
        self._ep = ep

    def _printOriginAutoloc3(self, org, extra=False):
        orid = org.publicID()

        arrivals = sortedArrivals(org)
        pick = picksForOrigin(org, self._ep)
        ampl = amplitudesForOrigin(org, self._ep)

        try:
            depthPhaseCount = org.quality().depthPhaseCount()
        except:
            depthPhaseCount = 0
            for arr in arrivals:
                wt = arr.weight()
                pha = arr.phase().code()
                #  if (pha[0] in ["p","s"] and wt >= 0.5 ):
                if (pha[0] in ["p", "s"] and wt >= self.minArrivalWeight):
                    depthPhaseCount += 1

        txt = ""

        evt = self._evt
        if not evt and self._ep:
            evt = eventForOrigin(orid, self._ep)

        if evt:
            txt += "Event:\n"
            txt += "    Public ID              %s\n" % evt.publicID()
            if extra:
                txt += "    Preferred Origin ID    %s\n" % evt.preferredOriginID()
                txt += "    Preferred Magnitude ID %s\n" % evt.preferredMagnitudeID()
            try:
                type = evt.type()
                txt += "    Type                   %s\n" % seiscomp.datamodel.EEventTypeNames.name(
                    type)
            except:
                pass
            txt += "    Description\n"
            for i in range(evt.eventDescriptionCount()):
                evtd = evt.eventDescription(i)
                evtdtype = seiscomp.datamodel.EEventDescriptionTypeNames.name(
                    evtd.type())
                txt += "      %s: %s" % (evtdtype, evtd.text())

            if extra:
                try:
                    txt += "\n    Creation time          %s\n" % evt.creationInfo().creationTime().toString("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            txt += "\n"
            preferredMagnitudeID = evt.preferredMagnitudeID()
        else:
            preferredMagnitudeID = ""

        tim = org.time().value()
        lat = org.latitude().value()
        lon = org.longitude().value()
        dep = org.depth().value()
        timerr = uncertainty(org.time())
        laterr = uncertainty(org.latitude())
        lonerr = uncertainty(org.longitude())
        deperr = uncertainty(org.depth())
        tstr = time2str(tim)

        originHeader = "Origin:\n"
        if evt:
            if org.publicID() != evt.preferredOriginID():
                originHeader = "Origin (NOT the preferred origin of this event):\n"

        txt += originHeader
        if extra:
            txt += "    Public ID              %s\n" % org.publicID()
        txt += "    Date                   %s\n" % tstr[:10]
        if timerr:
            if self.enhanced:
                txt += "    Time                   %s   +/- %8.3f s\n" % (
                    tstr[11:], timerr)
            else:
                txt += "    Time                   %s  +/- %6.1f s\n" % (
                    tstr[11:-2], timerr)
        else:
            if self.enhanced:
                txt += "    Time                   %s\n" % tstr[11:]
            else:
                txt += "    Time                   %s\n" % tstr[11:-2]

        if laterr:
            if self.enhanced:
                txt += "    Latitude              %10.5f deg  +/- %8.3f km\n" % (
                    lat, laterr)
            else:
                txt += "    Latitude              %7.2f deg  +/- %6.0f km\n" % (
                    lat, laterr)
        else:
            if self.enhanced:
                txt += "    Latitude              %10.5f deg\n" % lat
            else:
                txt += "    Latitude              %7.2f deg\n" % lat
        if lonerr:
            if self.enhanced:
                txt += "    Longitude             %10.5f deg  +/- %8.3f km\n" % (
                    lon, lonerr)
            else:
                txt += "    Longitude             %7.2f deg  +/- %6.0f km\n" % (
                    lon, lonerr)
        else:
            if self.enhanced:
                txt += "    Longitude             %10.5f deg\n" % lon
            else:
                txt += "    Longitude             %7.2f deg\n" % lon
        if self.enhanced:
            txt += "    Depth                %11.3f km" % dep
        else:
            txt += "    Depth                 %7.0f km" % dep
        if deperr is None:
            txt += "\n"
        elif deperr == 0:
            txt += "   (fixed)\n"
        else:
            if depthPhaseCount >= self.minDepthPhaseCount:
                if self.enhanced:
                    txt += "   +/- %8.3f km  (%d depth phases)\n" % (
                        deperr, depthPhaseCount)
                else:
                    txt += "   +/- %4.0f km  (%d depth phases)\n" % (
                        deperr, depthPhaseCount)
            else:
                if self.enhanced:
                    txt += "   +/- %8.3f km\n" % deperr
                else:
                    txt += "   +/- %4.0f km\n" % deperr

        agencyID = ""
        if self.useEventAgencyID:
            try:
                agencyID = evt.creationInfo().agencyID()
            except:
                pass
        else:
            try:
                agencyID = org.creationInfo().agencyID()
            except:
                pass
        txt += "    Agency                 %s\n" % agencyID
        if extra:
            try:
                authorID = org.creationInfo().author()
            except:
                authorID = "NOT SET"
            txt += "    Author                 %s\n" % authorID
        txt += "    Mode                   "
        try:
            txt += "%s\n" % seiscomp.datamodel.EEvaluationModeNames.name(
                org.evaluationMode())
        except:
            txt += "NOT SET\n"
        txt += "    Status                 "
        try:
            txt += "%s\n" % seiscomp.datamodel.EEvaluationStatusNames.name(
                org.evaluationStatus())
        except:
            txt += "NOT SET\n"

        if extra:
            txt += "    Creation time          "
            try:
                txt += "%s\n" % org.creationInfo().creationTime().toString("%Y-%m-%d %H:%M:%S")
            except:
                txt += "NOT SET\n"

        try:
            if self.enhanced:
                txt += "    Residual RMS           %9.3f s\n" % org.quality().standardError()
            else:
                txt += "    Residual RMS           %6.2f s\n" % org.quality().standardError()
        except:
            pass

        try:
            if self.enhanced:
                txt += "    Azimuthal gap           %8.1f deg\n" % org.quality().azimuthalGap()
            else:
                txt += "    Azimuthal gap           %5.0f deg\n" % org.quality().azimuthalGap()
        except:
            pass

        txt += "\n"

        networkMagnitudeCount = org.magnitudeCount()
        networkMagnitudes = {}

        # Each station magnitude contributes to the network
        # magnitude of the same type.
        #
        # We save here the StationMagnitudeContribution objects
        # by publicID of the corresponding StationMagnitude object.
        stationMagnitudeContributions = {}

        tmptxt = txt
        txt = ""
        foundPrefMag = False
        for i in range(networkMagnitudeCount):
            mag = org.magnitude(i)
            val = mag.magnitude().value()
            typ = mag.type()
            networkMagnitudes[typ] = mag

            for k in range(mag.stationMagnitudeContributionCount()):
                smc = mag.stationMagnitudeContribution(k)
                smid = smc.stationMagnitudeID()
                stationMagnitudeContributions[smid] = smc

            err = uncertainty(mag.magnitude())
            if err is not None:
                err = "+/- %.2f" % err
            else:
                err = ""

            if mag.publicID() == preferredMagnitudeID:
                preferredMarker = "preferred"
                foundPrefMag = True
            else:
                preferredMarker = "         "
            if extra:
                try:
                    agencyID = mag.creationInfo().agencyID()
                except:
                    pass
            else:
                agencyID = ""
            txt += "    %-8s %5.2f %8s %3d %s  %s\n" % \
                (typ, val, err, mag.stationCount(), preferredMarker, agencyID)

        if not foundPrefMag and preferredMagnitudeID != "":
            mag = seiscomp.datamodel.Magnitude.Find(preferredMagnitudeID)
#           if mag is None and self._dbq:
#               o = self._dbq.loadObject(
#                   seiscomp.datamodel.Magnitude.TypeInfo(), preferredMagnitudeID)
#               mag = seiscomp.datamodel.Magnitude.Cast(o)

            if mag:
                val = mag.magnitude().value()
                typ = mag.type()
                networkMagnitudes[typ] = mag

                err = uncertainty(mag.magnitude())
                if err is not None:
                    err = "+/- %.2f" % err
                else:
                    err = ""

                preferredMarker = "preferred"
                if extra:
                    try:
                        agencyID = mag.creationInfo().agencyID()
                    except:
                        pass
                else:
                    agencyID = ""
                txt += "    %-8s %5.2f %8s %3d %s  %s\n" % \
                    (typ, val, err, mag.stationCount(), preferredMarker, agencyID)

        txt = tmptxt + "%d Network magnitudes:\n" % networkMagnitudeCount + txt

        if not self._long:
            return txt

        lineFMT = "    %-5s %-2s  "
        if self.enhanced:
            lineFMT += "%9.3f" if self.distInKM else "%9.5f"
        else:
            lineFMT += "%5.0f" if self.distInKM else "%5.1f"
        lineFMT += " %s  %-7s %s %s %1s%1s %3.1f  "
        if self.polarities:
            lineFMT += "%s "
        lineFMT += "%-5s\n"

        dist_azi = {}
        lines = []

        for arr in arrivals:
            p = seiscomp.datamodel.Pick.Find(arr.pickID())
            if p is None:
                lines.append((180, "    ## missing pick %s\n" % arr.pickID()))
                continue

            if self.distInKM:
                dist = seiscomp.math.deg2km(arr.distance())
            else:
                dist = arr.distance()

            wfid = p.waveformID()
            net = wfid.networkCode()
            sta = wfid.stationCode()
            if self.enhanced:
                try:
                    azi = "%5.1f" % arr.azimuth()
                except:
                    azi = "  N/A"
                tstr = time2str(p.time().value())[11:]
                try:
                    res = "%7.3f" % arr.timeResidual()
                except:
                    res = "    N/A"
            else:
                try:
                    azi = "%3.0f" % arr.azimuth()
                except:
                    azi = "N/A"
                tstr = time2str(p.time().value())[11:-2]
                try:
                    res = "%5.1f" % arr.timeResidual()
                except:
                    res = "  N/A"
            dist_azi[net+"_"+sta] = (dist, azi)
            wt = arr.weight()
            pha = arr.phase().code()
            flag = "X "[wt > 0.1]
            try:
                status = seiscomp.datamodel.EEvaluationModeNames.name(p.evaluationMode())[
                    0].upper()
            except:
                status = "-"
            if self.polarities:
                try:
                    pol = seiscomp.datamodel.EPickPolarityNames.name(
                        p.polarity())
                except:
                    pol = None
                if pol:
                    if pol == "positive":
                        pol = "u"
                    elif pol == "negative":
                        pol = "d"
                    elif pol == "undecidable":
                        pol = "x"
                    else:
                        pol = "."
                else:
                    pol = "."
                line = lineFMT % (sta, net, dist, azi, pha,
                                  tstr, res, status, flag, wt, pol, sta)
            else:
                line = lineFMT % (sta, net, dist, azi, pha,
                                  tstr, res, status, flag, wt, sta)
            lines.append((dist, line))

        lines.sort()

        txt += "\n"
        txt += "%d Phase arrivals:\n" % org.arrivalCount()
        if self.enhanced:
            txt += "    sta   net      dist   azi  phase   time             res     wt  "
        else:
            txt += "    sta   net  dist azi  phase   time         res     wt  "
        if self.polarities:
            txt += "  "
        txt += "sta  \n"
        for dist, line in lines:
            txt += line
        txt += "\n"

        stationMagnitudeCount = org.stationMagnitudeCount()
        activeStationMagnitudeCount = 0
        stationMagnitudes = {}

        for i in range(stationMagnitudeCount):
            mag = org.stationMagnitude(i)
            typ = mag.type()
            if typ not in networkMagnitudes:
                continue
            if typ not in stationMagnitudes:
                stationMagnitudes[typ] = []

            # suppress unused station magnitudes
            smid = mag.publicID()
            if not smid in stationMagnitudeContributions:
                continue

            try:
                w = stationMagnitudeContributions[smid].weight()
            except:
                w = self.minStationMagnitudeWeight
            if w < self.minStationMagnitudeWeight:
                continue
            stationMagnitudes[typ].append(mag)
            activeStationMagnitudeCount += 1

        lineFMT = "    %-5s %-2s  "
        if self.enhanced:
            lineFMT += "%9.3f" if self.distInKM else "%9.5f"
        else:
            lineFMT += "%5.0f" if self.distInKM else "%5.1f"
        lineFMT += " %s  %-6s %5.2f %5.2f   %8s %4s\n"

        lines = []

        for typ in stationMagnitudes:
            for mag in stationMagnitudes[typ]:
                amplitudeID = mag.amplitudeID()
                if amplitudeID:
                    amp = seiscomp.datamodel.Amplitude.Find(amplitudeID)
                    if amp is None and self._dbq:
                        seiscomp.logging.debug(
                            "missing station amplitude '%s'" % amplitudeID)

                        # try to load amplitude from database
                        obj = self._dbq.loadObject(
                            seiscomp.datamodel.Amplitude.TypeInfo(),
                            amplitudeID)
                        amp = seiscomp.datamodel.Amplitude.Cast(obj)
                else:
                    # Station magnitude without associated amplitude.
                    # This is expected behaviour for some magnitudes
                    # like Me for which no amplitudes are stored.
                    amp = None

                p = ""
                a = "N/A"
                if amp:
                    try:
                        a = "%g" % amp.amplitude().value()
                    except:
                        a = "N/A"

                    if typ in ["mb", "Ms", "Ms(BB)"]:
                        try:
                            p = "%.2f" % amp.period().value()
                        except:
                            p = "N/A"
                    else:
                        p = ""

                wfid = mag.waveformID()
                net = wfid.networkCode()
                sta = wfid.stationCode()

                try:
                    dist, azi = dist_azi[net+"_"+sta]
                except:
                    dist, azi = 0, "  N/A" if self.enhanced else "N/A"

                val = mag.magnitude().value()
                res = val - networkMagnitudes[typ].magnitude().value()

                line = lineFMT % (sta, net, dist, azi, typ, val, res, a, p)
                lines.append((dist, line))

        lines.sort()

        if activeStationMagnitudeCount:
            txt += "%d Station magnitudes:\n" % activeStationMagnitudeCount
            if self.enhanced:
                txt += "    sta   net      dist   azi  type   value   res        amp  per\n"
            else:
                txt += "    sta   net  dist azi  type   value   res        amp  per\n"
            for dist, line in lines:
                txt += line
        else:
            txt += "No station magnitudes\n"

        return txt

    def printOrigin(self, origin):
        org = None
        if isinstance(origin, seiscomp.datamodel.Origin):
            org = origin
        elif isinstance(origin, str):
            for i in range(self._ep.originCount()):
                if self._ep.origin(i).publicID() == origin:
                    org = self._ep.origin(i)
#           if self._dbq:
#               org = self._dbq.loadObject(
#                   seiscomp.datamodel.Origin.TypeInfo(), origin)
#               org = seiscomp.datamodel.Origin.Cast(org)
#           if not org:
#               seiscomp.logging.error("origin '%s' not loaded" % origin)
#               return
        else:
            raise TypeError("illegal type for origin")

        if self.format == "autoloc3":
            return self._printOriginAutoloc3(org, extra=False)
        elif self.format == "autoloc3extra":
            return self._printOriginAutoloc3(org, extra=True)
        else:
            pass

    def printEvent(self, event):
        try:
            evt = None
            if isinstance(event, seiscomp.datamodel.Event):
                self._evt = event
                org = seiscomp.datamodel.Origin.Find(
                    event.preferredOriginID())
                if not org:
                    org = event.preferredOriginID()
                return self.printOrigin(org)
            elif isinstance(event, str):
                for i in range(self._ep.eventCount()):
                    if self._ep.event(i).publicID() == event:
                        evt = self._ep.event(i)
#               if self._dbq:
#                   evt = self._dbq.loadObject(
#                       seiscomp.datamodel.Event.TypeInfo(), event)
#                   evt = seiscomp.datamodel.Event.Cast(evt)
#                   self._evt = evt
                if evt is None:
                    raise TypeError("unknown event '" + event + "'")
                return self.printOrigin(evt.preferredOriginID())
            else:
                raise TypeError("illegal type for event")
        finally:
            self._evt = None

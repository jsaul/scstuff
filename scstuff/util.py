#!/usr/bin/env python
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

import seiscomp.core
import seiscomp.datamodel
import seiscomp.io
import seiscomp.logging
import operator
import sys
from math import pi


def readEventParametersFromXML(xmlFile="-"):
    """
    Reads an EventParameters root element from a SC XML file.

    The EventParameters instance holds all event parameters
    contained in the XML file. In particular there can be
    more than one event.
    """
    ar = seiscomp.io.XMLArchive()
    if xmlFile.lower().endswith(".gz"):
        ar.setCompression(True)
        ar.setCompressionMethod(seiscomp.io.XMLArchive.GZIP)
    if ar.open(xmlFile) is False:
        raise IOError(xmlFile + ": unable to open")
    obj = ar.readObject()
    if obj is None:
        raise TypeError(xmlFile + ": invalid format")
    ep  = seiscomp.datamodel.EventParameters.Cast(obj)
    if ep is None:
        raise TypeError(xmlFile + ": no eventparameters found")
    return ep


def writeEventParametersToXML(ep, xmlFile="-", formatted=True):
    ar = seiscomp.io.XMLArchive()
    ar.setFormattedOutput(formatted)
    if ar.create(xmlFile):
        ar.writeObject(ep)
        ar.close()
        return True
    return False


def EventParametersEvents(ep):
    for i in range(ep.eventCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        obj = seiscomp.datamodel.Event.Cast(ep.event(i))
        if obj:
            yield obj


def EventParametersOrigins(ep):
    for i in range(ep.originCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        obj = seiscomp.datamodel.Origin.Cast(ep.origin(i))
        if obj:
            yield obj


def EventParametersPicks(ep):
    for i in range(ep.pickCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        obj = seiscomp.datamodel.Pick.Cast(ep.pick(i))
        if obj:
            yield obj


def EventParametersAmplitudes(ep):
    for i in range(ep.amplitudeCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        obj = seiscomp.datamodel.Amplitude.Cast(ep.amplitude(i))
        if obj:
            yield obj


def EventParametersFocalMechanisms(ep):
    for i in range(ep.focalMechanismCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        obj = seiscomp.datamodel.FocalMechanism.Cast(ep.focalMechanism(i))
        if obj:
            yield obj


def extractEventParameters(ep, eventID=None, filterOrigins=False, filterPicks=False):
    """
    Extract picks, amplitudes, origins, events and focal mechanisms
    from an EventParameters instance.

    Returns a tuple of dicts. Each dict contains the objects of the
    given type, with their publicID used as key.
    """
    pick  = {}
    ampl  = {}
    event = {}
    origin = {}
    fm = {}

    for obj in EventParametersEvents(ep):
        publicID = obj.publicID()
        if eventID is not None and publicID != eventID:
            continue
        event[publicID] = obj

    for obj in EventParametersOrigins(ep):
        publicID = obj.publicID()
        if filterOrigins:
            # For each event only keep the preferredOrigin.
            for _eventID in event:
                if publicID == event[_eventID].preferredOriginID():
                    origin[publicID] = org = obj
                    break

        else:
            origin[publicID] = obj

    # Track which picks are referenced by origins.
    pickIDs = []
    for publicID in origin:
        org = origin[publicID]
        for i in range(org.arrivalCount()):
            arr = org.arrival(i)
            pickIDs.append(arr.pickID())

    for obj in EventParametersPicks(ep):
        publicID = obj.publicID()
        if filterPicks and publicID not in pickIDs:
            continue
        pick[publicID] = obj

    for obj in EventParametersAmplitudes(ep):
        if obj.pickID() not in pick:
            continue
        ampl[obj.publicID()] = obj

    for obj in EventParametersFocalMechanisms(ep):
        fm[obj.publicID()] = obj

    return event, origin, pick, ampl, fm


def EventParametersIterator(ep):
    """
    Iterates over all public objects in an EventParameters instance
    """
    for i in range(ep.eventCount()):
        yield ep.event(i)
    for i in range(ep.originCount()):
        org = ep.origin(i)
        for k in range(org.magnitudeCount()):
            mag = org.magnitude(k)
            yield mag
        for k in range(org.stationMagnitudeCount()):
            mag = org.stationMagnitude(k)
            yield mag
        for k in range(org.arrivalCount()):
            arr = org.arrival(k)
            yield arr
        yield org
    for i in range(ep.pickCount()):
        yield ep.pick(i)
    for i in range(ep.amplitudeCount()):
        yield ep.amplitude(i)
    for i in range(ep.focalMechanismCount()):
        fm = ep.focalMechanism(i)
        for k in range(fm.momentTensorCount()):
            mt = fm.momentTensor(k)
            yield mt
        yield fm


def ep_get_event(ep, eventID):

    for evt in EventParametersEvents(ep):
        publicID = evt.publicID()
        if publicID == eventID:
            return evt


def ep_get_origin(ep, eventID=None, originID=None):

    if eventID:
        evt = ep_get_event(ep, eventID)
        if not evt:
            return
    else:
        evt = None

    for i in range(ep.originCount()):
        # FIXME: The cast hack forces the SC refcounter to be increased.
        org = seiscomp.datamodel.Origin.Cast(ep.origin(i))
        if originID is None:
            if evt is not None:
                if org.publicID() == evt.preferredOriginID():
                    return org
        else:
            if originID == org.publicID():
                return org


def ep_get_magnitude(ep, eventID):

    evt = ep_get_event(ep, eventID)
    if not evt:
        return
    mag = seiscomp.datamodel.Magnitude.Find(evt.preferredMagnitudeID())
    return mag


def ep_get_fm(ep, eventID):
    """
    retrieve the "preferred" moment tensor from EventParameters
    object ep for event with the specified public ID
    """
    evt = ep_get_event(ep, eventID)
    if not evt:
        return
    fm = seiscomp.datamodel.FocalMechanism.Find(evt.preferredFocalMechanismID())
    return fm


def ep_get_region(ep, eventID):

    evt = ep_get_event(ep, eventID)
    if not evt:
        return
    for i in range(evt.eventDescriptionCount()):
        evtd = evt.eventDescription(i)
        evtdtype = seiscomp.datamodel.EEventDescriptionTypeNames.name(evtd.type())
        evtdtext = evtd.text()
        if evtdtype.startswith("region"):
            return evtdtext


def nslc(obj):
    """
    Convenience function to retrieve network, station, location and
    channel codes from a waveformID object and return them as tuple
    """
    if isinstance(obj, seiscomp.datamodel.WaveformStreamID) or \
       isinstance(obj, seiscomp.core.Record):
        n = obj.networkCode()
        s = obj.stationCode()
        l = obj.locationCode()
        c = obj.channelCode()
    else:
        return nslc(obj.waveformID())
    return n, s, l, c


def format_nslc_spaces(wfid):
    """
    Convenience function to return network, station, location and channel code as fixed-length, space-separated string
    """
    n,s,l,c = nslc(wfid)
    if l=="": l="--"
    return "%-2s %5s %2s %3s" % (n,s,l,c)


def format_nslc_dots(wfid):
    """
    Convenience function to return network, station, location and channel code as dot-separated string
    """
    return "%s.%s.%s.%s" % nslc(wfid)


def isotimestamp(time, digits=3):
    """
    Convert a seiscomp.core.Time to a timestamp YYYY-MM-DDTHH:MM:SS.sssZ
    """
    return time.toString("%Y-%m-%dT%H:%M:%S.%f000000")[:20+digits].strip(".")+"Z"


def format_time(time, digits=3):
    """
    Convert a seiscomp.core.Time to a string
    """
    return time.toString("%Y-%m-%d %H:%M:%S.%f000000")[:20+digits].strip(".")


def automatic(obj):
    return obj.evaluationMode() == seiscomp.datamodel.AUTOMATIC


def parseTime(s):
    for fmtstr in "%FT%TZ", "%FT%T.%fZ", "%F %T", "%F %T.%f":
        t = seiscomp.core.Time.GMT()
        if t.fromString(s, fmtstr):
            return t
    raise ValueError("could not parse time string '%s'" %s)


def removeComments(obj):
    """
    Remove all comments from the specified object and its children
    """
    if obj is None:
        return

    tobj = type(obj)

    if tobj in [
        seiscomp.datamodel.Event,
        seiscomp.datamodel.Magnitude,
        seiscomp.datamodel.StationMagnitude,
        seiscomp.datamodel.MomentTensor,
        seiscomp.datamodel.Amplitude,
        seiscomp.datamodel.Pick ]:

        while obj.commentCount() > 0:
            obj.removeComment(0)
        return

    if tobj is seiscomp.datamodel.Origin:
        while obj.commentCount() > 0:
            obj.removeComment(0)
        for k in range(obj.magnitudeCount()):
            removeComments(obj.magnitude(k))
        for k in range(obj.stationMagnitudeCount()):
            removeComments(obj.stationMagnitude(k))
        # Note that SeisComP Arrival's have no comments

    if tobj is seiscomp.datamodel.FocalMechanism:
        while obj.commentCount() > 0:
            obj.removeComment(0)
        for k in range(obj.momentTensorCount()):
            removeComments(obj.momentTensor(k))

    if tobj is seiscomp.datamodel.EventParameters:
        for i in range(obj.eventCount()):
            removeComments(obj.event(i))
        for i in range(obj.originCount()):
            removeComments(obj.origin(i))
        for i in range(obj.pickCount()):
            removeComments(obj.pick(i))
        for i in range(obj.amplitudeCount()):
            removeComments(obj.amplitude(i))
        for i in range(obj.focalMechanismCount()):
            removeComments(obj.focalMechanism(i))


def recursivelyRemoveComments(ep):
    removeComments(ep)


def _removeAuthor(obj):
    try:
        # Only if the object has a creationInfo
        # AND the creationInfo has an author
        c = obj.creationInfo()
        a = obj.creationInfo().author()
        if len(a) > 0:
            obj.creationInfo().setAuthor("")
    except:
        pass


def removeAuthorInfo2(obj):
    """
    Remove all author information from the specified object and its children
    """
    if obj is None:
        return

    tobj = type(obj)

    if tobj in [
        seiscomp.datamodel.Event,
        seiscomp.datamodel.Magnitude,
        seiscomp.datamodel.StationMagnitude,
        seiscomp.datamodel.MomentTensor,
        seiscomp.datamodel.Amplitude,
        seiscomp.datamodel.Pick ]:

        _removeAuthor(obj)
        return

    if tobj is seiscomp.datamodel.Origin:
        _removeAuthor(obj)
        for k in range(obj.magnitudeCount()):
            removeAuthorInfo(obj.magnitude(k))
        for k in range(obj.stationMagnitudeCount()):
            removeAuthorInfo(obj.stationMagnitude(k))
        # Note that SeisComP Arrival's have no comments

    if tobj is seiscomp.datamodel.FocalMechanism:
        _removeAuthor(obj)
        for k in range(obj.momentTensorCount()):
            removeAuthorInfo(obj.momentTensor(k))

    if tobj is seiscomp.datamodel.EventParameters:
        for i in range(obj.eventCount()):
            removeAuthorInfo(obj.event(i))
        for i in range(obj.originCount()):
            removeAuthorInfo(obj.origin(i))
        for i in range(obj.pickCount()):
            removeAuthorInfo(obj.pick(i))
        for i in range(obj.amplitudeCount()):
            removeAuthorInfo(obj.amplitude(i))
        for i in range(obj.focalMechanismCount()):
            removeAuthorInfo(obj.focalMechanism(i))


def removeAuthorInfo(ep):
    """
    Remove all author information from the specified EventParameters
    instance and its children
    """

    emptyAuthor = ""

    for obj in EventParametersIterator(ep):
        try:
            ci = obj.creationInfo()
        except:
            continue
        ci.setAuthor(emptyAuthor)
        obj.setCreationInfo(ci)


def stripOrigin(origin):
    """
    Remove all arrivals and magnitudes from the origin.
    
    An origin loaded using query().getObject() is already
    "naked" and this operation is not needed.
    """
    while origin.arrivalCount() > 0:
        origin.removeArrival(0)
    while origin.magnitudeCount() > 0:
        origin.removeMagnitude(0)
    while origin.stationMagnitudeCount() > 0:
        origin.removeStationMagnitude(0)


def sortedByCreationTime(objects):
    """
    Return the objects sorted by their creation time in ascending
    order. For each of the objects, creationInfo.creationTime is
    required to be available.
    """
    tmp = []
    for obj in objects:
        t = obj.creationInfo().creationTime()
        tmp.append( (t, obj) )
    tmp.sort(key=operator.itemgetter(0))
    return [ o for (t, o) in tmp ]


def statusFlag(obj):
    """
    If the object is 'manual', return 'M' otherwise 'A'.
    """
    try:
        if obj.evaluationMode() == seiscomp.datamodel.MANUAL:
            return "M"
    except:
        pass
    return "A"


status = statusFlag


def manualPickCount(origin, minWeight=0.5):
    """
    Count the manual picks contributing to the origin. Picks
    contribute to the origin if the arrival.weight >= minWeight.

    This requires the picks to be reachable via Pick.Find() i.e.
    through the public object registry. If not registered, a pick
    cannot be found.
    """
    count = 0
    for i in range(origin.arrivalCount()):
        a = origin.arrival(i)
        if a.weight() < 0.5:
            continue
        pid = a.pickID()
        p = seiscomp.datamodel.Pick.Find(pid)
        if not p:
            # might be more appropriate to raise an exception
            seiscomp.logging.warning("Pick %s could not be found" % pid)
            continue
        if status(p) != "M":
            continue
        count += 1
    return count


def RecordIterator(recordstream, showprogress=False):
        count = 0
        # It would be desirable to not need to unpack the records.
        # Just pass around the raw records.
        inp = seiscomp.io.RecordInput(
                    recordstream,
                    seiscomp.core.Array.INT,
                    seiscomp.core.Record.SAVE_RAW)
        while True:
            try:
                rec = inp.next()
            except Exception as exc:
                seiscomp.logging.error(str(exc))
                rec = None

            if not rec:
                break
            if showprogress:
                count += 1
                sys.stderr.write("%-20s %6d\r" % (rec.streamID(), count))
            yield rec


pz_header_template = """* **********************************
* NETWORK   (KNETWK): %(net)s
* STATION    (KSTNM): %(sta)s
* LOCATION   (KHOLE): %(loc)s
* CHANNEL   (KCMPNM): %(cha)s
* CREATED           : %(creation_date)s
* START             : %(start_date)s
* END               : %(end_date)s
* DESCRIPTION       : %(description)s
* LATITUDE          : %(lat).6f
* LONGITUDE         : %(lon).6f
* ELEVATION         : %(ele).1f
* DEPTH             : %(depth).1f
* DIP               : %(dip).1f
* DIP (SEED)        : %(dip_seed).1f
* AZIMUTH           : %(azimuth).1f
* SAMPLE RATE       : %(fsamp).1g
* INPUT UNIT        : %(input_unit)s
* OUTPUT UNIT       : %(output_unit)s
* INSTTYPE          : %(sensor_type)s
* INSTGAIN          : %(inst_gain).6e (%(inst_gain_unit)s)
* INSTGAIN FREQ     : %(sensitivity_frequency)g
* SENSITIVITY       : %(sensitivity_value).6e (%(sensitivity_unit)s)
* SENSITIVITY FREQ  : %(sensitivity_frequency)g
* A0                : %(a0).6e
* **********************************
"""

valid_units = { "M":0, "M/S":1, "M/S**2":2 }


def rectifyUnit(unit):
    unit = unit.upper()
    # for accelerometers several unit strings have been
    # seen in the wild. We don't want to support them all.
    if unit in [ "M/S/S", "M/S^2" ]:
        unit = "M/S**2"
    if unit not in valid_units:
        raise ValueError("Invalid ground motion unit"+unit)
    return unit


def sacpz(network, station, location, stream, configured=None):
    net = network.code()
    sta = station.code()
    loc = location.code()
    cha = stream.code()
    if loc.strip() == "":
        loc = "--"

    if configured and (net, sta, loc, cha[:2]) not in configured:
        return

    now = seiscomp.core.Time.GMT()

    pz = {
        "net": net,
        "sta": sta,
        "loc": loc,
        "cha": cha,
        "lat": location.latitude(),
        "lon": location.longitude(),
        "ele": location.elevation(),
        "creation_date" : now.toString("%FT%TZ")
    }

    item = "%s.%s.%s.%s" % (net, sta, loc, cha)
    sensor = seiscomp.datamodel.Sensor.Find(stream.sensor())
    if not sensor:
        seiscomp.logging.warning("no sensor for   " + item)
        return
    response = seiscomp.datamodel.PublicObject.Find(sensor.response())
    if not response:
        seiscomp.logging.warning("no response for " + item)
        return
    paz = seiscomp.datamodel.ResponsePAZ.Cast(response)
    if not paz:
        seiscomp.logging.warning("no paz for      " + item)
        return

    try:
        norm = paz.normalizationFactor()
    except ValueError:
        seiscomp.logging.warning(
            "ResponsePAZ.normalizationFactor missing for " + item)
        norm = None

    try:
        if paz.numberOfPoles():
            poles = paz.poles().content()
        else:
            poles = []
    except ValueError:
        seiscomp.logging.warning(
            "ResponsePAZ.poles               missing for " + item)
        poles = None

    try:
        if paz.numberOfZeros():
            zeros = paz.zeros().content()
        else:
            zeros = []
    except ValueError:
        seiscomp.logging.warning(
            "ResponsePAZ.zeros               missing for " + item)
        zeros = None

    if norm is None or zeros is None or poles is None:
        return

    if paz.type() == "A":
        f = 1
    elif paz.type() == "B":
        f = 2*pi
        n = len(poles)-len(zeros)
        norm *= f**n
    else:
        seiscomp.logging.error("unknown paz type for " + item)
        return
    pz["inst_gain"] = paz.gain()
#   pz["inst_gain_unit"] = "inst_gain_unit unknown"
    pz["inst_gain_frequency"] = paz.gainFrequency()
    poles = [ f*poles[i] for i in range(len(poles)) ]
    zeros = [ f*zeros[i] for i in range(len(zeros)) ]
    input_unit = rectifyUnit(sensor.unit().upper())
    if input_unit == "M/S":
        # if input unit is velocity, we need to convert it to
        # displacement as this is implied in the SAC PAZ format.
        zeros.append(0)
        input_unit = "M"
    pz["input_unit"] = input_unit
    pz["a0"] = norm
    try:
        pz["start_date"] = stream.start().toString("%FT%TZ")
    except:
        pass

    try:
        pz["end_date"] = stream.end().toString("%FT%TZ")
    except:
        pass


    try:
        pz["description"] = station.description()
        # or station.description()
    except:
        pass

    try:
        pz["depth"] = stream.depth()
    except:
        pass

    try:
        # SAC and SEED unfortunately use different
        # conventions for dip. We support both, also
        # to make this fact clear to the unsuspecting
        # user.
        pz["dip"]      = stream.dip() + 90
        pz["dip_seed"] = stream.dip()
    except:
        pass

# The dip of the instrument in degrees, down from horizontal.
# The azimuth and the dip describe the direction of the sensitive axis of the instrument (if applicable). Motion
# in the same direction as this axis is positive. SEED provides this field for non-traditional instruments or for
#traditional instruments that have been oriented in some non-traditional way. Here are traditional orientations:
# Z — Dip -90, Azimuth 0 (Reversed: Dip 90, Azimuth 0)
# N — Dip 0, Azimuth 0 (Reversed: Dip 0, Azimuth 180)
# E — Dip 0, Azimuth 90 (Reversed: Dip 0, Azimuth 270)



    try:
        pz["azimuth"] = stream.azimuth()
    except:
        pass

    try:
        n = stream.sampleRateNumerator()
        d = stream.sampleRateDenominator()
        pz["fsamp"] = n/d
    except:
        pass

    try:
        pz["sensitivity_value"] = stream.gain()
        pz["sensitivity_unit"] = rectifyUnit(stream.gainUnit().upper())
        pz["sensitivity_frequency"] = stream.gainFrequency()
    except:
        pass

    pz["output_unit"] = "COUNTS"

    try:
        # pz["sensor_type"] = sensor.type()
        pz["sensor_type"] = sensor.description()
    except:
        pass

    try:
        pz["sensor_gain"] = sensor.gain()
    except:
        pass

    lines = []
    for line in pz_header_template.split("\n"):
        try:
            line = line % pz
        except:
            continue
        lines.append(line)

    s = "\n".join(lines)

    s += "ZEROS\t%d\n" % len(zeros)
    for zero in sorted(zeros, key=abs):
        s += "\t%+.6e\t%+.6e\n" % (zero.real, zero.imag)
    s += "POLES\t%d\n" % len(poles)
    for pole in sorted(poles, key=abs):
        s += "\t%+.6e\t%+.6e\n" % (pole.real, pole.imag)
    s += "CONSTANT %.6e\n" % (pz["a0"]*pz["sensitivity_value"])

    return s


def ArrivalIterator(origin):
    for i in range(origin.arrivalCount()):
        yield origin.arrival(i)


def configuredStreams(configModule, setupName):
    """
    Get the configured streams from the specified config module.

    Returns a list of n,s,l,c tuples, where c is the two-letter stream code,
    i.e. SEED channel code without component code (e.g. "BH" for "BHZ").
    """
    items = []
    for i in range(configModule.configStationCount()):
        cfg = configModule.configStation(i)
        setup = seiscomp.datamodel.findSetup(cfg, setupName, True)
        if not setup: continue

        params = seiscomp.datamodel.ParameterSet.Find(setup.parameterSetID())
        if not params: continue

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

        item = (cfg.networkCode(), cfg.stationCode(), detecLocid, detecStream)
        items.append(item)

    return items


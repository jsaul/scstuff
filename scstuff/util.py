#!/usr/bin/env python
# -*- coding: utf-8 -*-

import seiscomp.core, seiscomp.datamodel, seiscomp.io, seiscomp.logging
import operator

def readEventParametersFromXML(xmlFile="-"):
    """
    Reads an EventParameters root element from a SC3 XML file. The
    EventParameters instance holds all event parameters as child
    elements.
    """
    ar = seiscomp.io.XMLArchive()
    if ar.open(xmlFile) == False:
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
        obj = seiscomp.datamodel.Event.Cast(ep.event(i))
        if obj:
            yield obj

def EventParametersOrigins(ep):
    for i in range(ep.originCount()):
        obj = seiscomp.datamodel.Origin.Cast(ep.origin(i))
        if obj:
            yield obj

def EventParametersPicks(ep):
    for i in range(ep.pickCount()):
        obj = seiscomp.datamodel.Pick.Cast(ep.pick(i))
        if obj:
            yield obj

def EventParametersAmplitudes(ep):
    for i in range(ep.amplitudeCount()):
        obj = seiscomp.datamodel.Amplitude.Cast(ep.amplitude(i))
        if obj:
            yield obj

def EventParametersFocalMechanisms(ep):
    for i in range(ep.focalMechanismCount()):
        obj = seiscomp.datamodel.FocalMechanism.Cast(ep.focalMechanism(i))
        if obj:
            yield obj


def extractEventParameters(ep, eventID=None, filterOrigins=False, filterPicks=False):
    """
    Extract picks, amplitudes, origins, events and focal mechanisms
    from an EventParameters instance. 

    NOTE than the EventParameters is modified; extracted objects are removed.
    """
    pick  = {}
    ampl  = {}
    event = {}
    origin = {}
    fm = {}

#   while ep.eventCount() > 0:
#       # FIXME: The cast hack forces the SC3 refcounter to be increased.
#       obj = seiscomp.datamodel.Event.Cast(ep.event(0))
#       ep.removeEvent(0)
    for obj in EventParametersEvents(ep):
        publicID = obj.publicID()
        if eventID is not None and publicID != eventID:
            continue
        event[publicID] = obj

    pickIDs = []
#   while ep.originCount() > 0:
#       # FIXME: The cast hack forces the SC3 refcounter to be increased.
#       obj = seiscomp.datamodel.Origin.Cast(ep.origin(0))
#       ep.removeOrigin(0)
    for obj in EventParametersOrigins(ep):
        publicID = obj.publicID()
        if filterOrigins:
            # only keep origins that are preferredOrigin's of an event
            for _eventID in event:
                if publicID == event[_eventID].preferredOriginID():
                    origin[publicID] = org = obj
                    # collect pick ID's for all associated picks
                    for i in range(org.arrivalCount()):
                        arr = org.arrival(i)
                        pickIDs.append(arr.pickID())
                    break

        else:
            origin[publicID] = obj

#   while ep.pickCount() > 0:
#       # FIXME: The cast hack forces the SC3 refcounter to be increased.
#       obj = seiscomp.datamodel.Pick.Cast(ep.pick(0))
#       ep.removePick(0)
    for obj in EventParametersPicks(ep):
        publicID = obj.publicID()
        if filterPicks and publicID not in pickIDs:
            continue
        pick[publicID] = obj

#   while ep.amplitudeCount() > 0:
#       # FIXME: The cast hack forces the SC3 refcounter to be increased.
#       obj = seiscomp.datamodel.Amplitude.Cast(ep.amplitude(0))
#       ep.removeAmplitude(0)
    for obj in EventParametersAmplitudes(ep):
        if obj.pickID() not in pick:
            continue
        ampl[obj.publicID()] = obj

#   while ep.focalMechanismCount() > 0:
#       # FIXME: The cast hack forces the SC3 refcounter to be increased.
#       obj = seiscomp.datamodel.FocalMechanism.Cast(ep.focalMechanism(0))
#       ep.removeFocalMechanism(0)
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

    for i in range(ep.originCount()):
        # FIXME: The cast hack forces the SC3 refcounter to be increased.
        org = seiscomp.datamodel.Origin.Cast(ep.origin(i))
        if originID is None:
            if event is not None:
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


def nslc(wfid):
    """
    Convenience function to retrieve network, station, location and channel codes from a waveformID object and return them as tuple
    """
    n,s,l,c = wfid.networkCode(),wfid.stationCode(),wfid.locationCode(),wfid.channelCode()
    return n,s,l,c


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
    return time.toString("%Y-%m-%dZ%H:%M:%S.%f000000")[:20+digits].strip(".")+"Z"


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
        for i in range(ep.eventCount()):
            removeAuthorInfo(ep.event(i))
        for i in range(ep.originCount()):
            removeAuthorInfo(ep.origin(i))
        for i in range(ep.pickCount()):
            removeAuthorInfo(ep.pick(i))
        for i in range(ep.amplitudeCount()):
            removeAuthorInfo(ep.amplitude(i))
        for i in range(ep.focalMechanismCount()):
            removeAuthorInfo(ep.focalMechanism(i))


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
    return [ o for (t,o) in tmp ]


def status(obj):
    try:
        if obj.evaluationMode() == seiscomp.datamodel.MANUAL:
            return "M"
    except:
        pass
    return "A"


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


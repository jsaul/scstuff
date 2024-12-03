#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-

import seiscomp.client
import seiscomp.datamodel
import seiscomp.io
import scstuff.util


from seiscomp.datamodel import \
    EventParameters, Event, \
    Origin, OriginReference, \
    FocalMechanism, FocalMechanismReference, \
    Magnitude, Pick, Amplitude, CreationInfo


def loadEvent(query, publicID, full=True):
    """
    Retrieve an event from DB

    Returns either the event instance or None if it could not be loaded.

    If full==False, getObject() is used, which is very fast as it
    doesn't load all children. Children included anyway are
        preferredOriginID
        preferredMagnitudeID
        preferredFocalMechanismID
        creationInfo

    if full==True, loadObject() is used to additionally load the children:
        comment
        description
        originReference
        focalMechanismReference
    """

    load = query.loadObject if full else query.getObject

    obj = load(seiscomp.datamodel.Event.TypeInfo(), publicID)
    obj = seiscomp.datamodel.Event.Cast(obj)

    return obj  # may be None


def loadOrigin(query, publicID, full=True):
    """
    Retrieve an origin from DB

    Returns either the origin instance or None if it could not be loaded.

    If full==False, getObject() is used, which is very fast as it
    doesn't load all children. Children included anyway are
        creationInfo
        quality
        uncertainty

    if full==True, loadObject() is used to additionally load the children:
        arrival
        comment
        magnitude
        stationMagnitude
    """

    load = query.loadObject if full else query.getObject
    obj = load(seiscomp.datamodel.Origin.TypeInfo(), publicID)
    obj = seiscomp.datamodel.Origin.Cast(obj)
    return obj  # may be None


def loadMagnitude(query, publicID, full=True):
    """
    Retrieve a magnitude from DB

    Returns either the magnitude instance or None if it could not be loaded.

    If full==False, getObject() is used, which is very fast as it
    doesn't load all children. Children included anyway are
        creationInfo

    if full==True, loadObject() is used to additionally load the children:
        comment
    """

    load = query.loadObject if full else query.getObject
    obj = load(seiscomp.datamodel.Magnitude.TypeInfo(), publicID)
    obj = seiscomp.datamodel.Magnitude.Cast(obj)
    return obj  # may be None


def loadFocalMechanism(query, publicID, full=True):
    """
    Retrieve a focal mechanism from DB

    Returns either the focal mechanism instance or None if it could not
    be loaded.

    If full==False, getObject() is used, which is very fast as it
    doesn't load all children. Children included anyway are
        creationInfo
        nodalPlanes
        principalAxes

    if full==True, loadObject() is used to additionally load the children:
        comment
        momentTensor

    Note that even with full==True, the moment magnitude is not loaded
    automatically. There is a derivedOriginID, which refers to an origin
    that must be loaded separately with loadOrigin(..., full=True) and
    which then contains the moment magnitude as child.
    """
    load = query.loadObject if full else query.getObject
    obj = load(seiscomp.datamodel.FocalMechanism.TypeInfo(), publicID)
    obj = seiscomp.datamodel.FocalMechanism.Cast(obj)
    return obj  # may be None


def loadOriginsForEvent(query, publicID, full=False):
    """
    Retrieve all origins from DB for an event with given publicID.

    The issue with DatabaseQuery.getOrigins() is that it does not retrieve
    Origin objects for which there is no OriginReference. Origins like that
    are referred to e.g. by FocalMechanism's and MomentTensor's.

    In a second query it also retrieves the FocalMechanism's, loads the
    MomentTensor children and the Origin's referenced from there.

    Warning: This can be slow if full==True and if there are many origins.
    """
    origins = list()
    for origin in query.getOrigins(publicID):
        origin = seiscomp.datamodel.Origin.Cast(origin)
        if not origin:
            continue
        origins.append(origin)

    focalMechanisms = list()
    for focalMechanism in query.getFocalMechanismsDescending(publicID):
        focalMechanism = seiscomp.datamodel.FocalMechanism.Cast(focalMechanism)
        focalMechanisms.append(focalMechanism)
    for focalMechanism in focalMechanisms:
        query.loadMomentTensors(focalMechanism)
        momentTensorCount = focalMechanism.momentTensorCount()
        for i in range(momentTensorCount):
            momentTensor = focalMechanism.momentTensor(i)
            derivedOriginID = momentTensor.derivedOriginID()
            if derivedOriginID:
                origin = loadOrigin(query, derivedOriginID, full=False)
            origins.append(origin)

    if not full:
        return origins

    fullOrigins = list()
    for origin in origins:
        fullOrigin = loadOrigin(query, origin.publicID(), full=full)
        fullOrigins.append(fullOrigin)

    return full_origins


getOrigins = loadOriginsForEvent


def loadFocalMechanismsForEvent(query, publicID, full=False):
    """
    Retrieve all focal mechanisms from DB for an event with given publicID.
    """
    focalMechanisms = list()
    for focalMechanism in query.getFocalMechanismsDescending(publicID):
        focalMechanism = seiscomp.datamodel.FocalMechanism.Cast(focalMechanism)
        focalMechanisms.append(focalMechanism)

    if not full:
        return focalMechanisms

    fullFocalMechanisms = list()
    for focalMechanism in focalMechanisms:
        fullFocalMechanism = loadfocalMechanism(query, focalMechanism.publicID(), full=full)
        fullFocalMechanisms.append(fullFocalMechanism)

    return fullFocalMechanisms


stripAuthorInfo = scstuff.util.stripAuthorInfo
stripCreationInfo = scstuff.util.stripCreationInfo
stripOrigin = scstuff.util.stripOrigin
stripMomentTensor = scstuff.util.stripMomentTensor


def loadCompleteEvent(
        query, eventID,
        preferredOriginID=None,
        preferredMagnitudeID=None,
        preferredFocalMechanismID=None,
        comments=False, allmagnitudes=False,
        withPicks=False, preferred=False):
    """
    Load a "complete" event from the database via the specified
    query.

    "Complete" here means Event with preferred Origin, Magnitude,
    FocalMechanism, Picks, Amplitudes, etc. but not all Origins etc.
    Only what filly represents all the preferred children.

    It is possible to override the preferredOriginID,
    preferredMagnitudeID and preferredFocalMechanismID.

    Things to do:
    * load event
    * load preferred origin without arrivals
    * load at least the preferred magnitude if available, all
      magnitudes if requested
    * load focal mechanism incl. moment tensor depending on availability,
      incl. Mw from derived origin
    """

    ep = EventParameters()

    # Load event and preferred origin. This is the minimum
    # required info and if it can't be loaded, give up.
    event = loadEvent(query, eventID)
    if event is None:
        raise ValueError("unknown event '" + eventID + "'")

    # We have the possibility to override the preferredOriginID etc.
    # but need to do this at the beginning.
    if preferredOriginID:
        event.setPreferredOriginID(preferredOriginID)
    if preferredMagnitudeID:
        event.setPreferredMagnitudeID(preferredMagnitudeID)
    if preferredFocalMechanismID:
        event.setPreferredFocalMechanismID(preferredFocalMechanismID)

    origins = dict()
    focalMechanisms = dict()

    preferredOrigin = None
    preferredFocalMechanism = None


    # Load all origins that are children of EventParameters. Currently
    # this does not load derived origins because for these there is no
    # originReference created, which is probably a bug. FIXME!
    for origin in query.getOrigins(eventID):
        origin = Origin.Cast(origin)
        # The origin is bare minimum without children.
        # No arrivals, magnitudes, comments... will load those later.
        if not origin:
            continue
        origins[origin.publicID()] = origin

    # Load all focal mechanisms and then load moment tensor children
    for focalMechanism in query.getFocalMechanismsDescending(eventID):
        focalMechanism = FocalMechanism.Cast(focalMechanism)
        if not focalMechanism:
            continue
        focalMechanisms[focalMechanism.publicID()] = focalMechanism
    for focalMechanismID in focalMechanisms:
        focalMechanism = focalMechanisms[focalMechanismID]
        query.loadMomentTensors(focalMechanism)
        # query.loadComments(focalMechanism)

    # Load triggering and derived origins for all focal mechanisms and moment tensors
    #
    # A derived origin may act as a triggering origin of another focal mechanisms.
    for focalMechanismID in focalMechanisms:
        focalMechanism = focalMechanisms[focalMechanismID]

        for i in range(focalMechanism.momentTensorCount()):
            momentTensor = focalMechanism.momentTensor(i)
            if momentTensor.derivedOriginID():
                derivedOriginID = momentTensor.derivedOriginID()
                # assert derivedOriginID not in origins

                if derivedOriginID not in origins:
                    derivedOrigin = loadOrigin(query, derivedOriginID)
                    if derivedOrigin is None:
                        seiscomp.logging.warning("%s: failed to load derived origin %s" % (eventID, derivedOriginID))
                    else:
                        stripOrigin(derivedOrigin)
                        origins[derivedOriginID] = derivedOrigin

        triggeringOriginID = focalMechanism.triggeringOriginID()
        if triggeringOriginID not in origins:
            # Actually not unusual. Happens if a derived origin is used as
            # triggering origin, as for the derived origins there is no
            # OriginReference. So rather than a warning we only issue a
            # debug message.
            #
            msg = "%s: triggering origin %s not in origins" % (eventID, triggeringOriginID)
            seiscomp.logging.debug(msg)
            triggeringOrigin = loadOrigin(query, triggeringOriginID)
            if triggeringOrigin is None:
                msg = "%s: failed to load triggering origin %s" % (eventID, triggeringOriginID)
                seiscomp.logging.warning(msg)
            else:
                stripOrigin(triggeringOrigin)
                origins[triggeringOriginID] = triggeringOrigin

    # Load arrivals, comments, magnitudes into origins
    for originID in origins:
        origin = origins[originID]

        if withPicks:
            query.loadArrivals(origin)
        if comments:
            query.loadComments(origin)
        query.loadMagnitudes(origin)

    if event.preferredOriginID():
        preferredOriginID = event.preferredOriginID()
    else:
        preferredOriginID = None

    if preferredOrigin is None:
        if preferredOriginID and preferredOriginID in origins:
            preferredOrigin = origins[preferredOriginID]
        if preferredOrigin is None:
            raise RuntimeError(
                "preferred origin '" + preferredOriginID + "' not found")

    # Load all magnitudes for all loaded origins
    magnitudes = dict()
    if allmagnitudes:
        for originID in origins:
            origin = origins[originID]
            for i in range(origin.magnitudeCount()):
                magnitude = origin.magnitude(i)
                magnitudes[magnitude.publicID()] = magnitude

    preferredMagnitude = None
    if event.preferredMagnitudeID():
        if event.preferredMagnitudeID() in magnitudes:
            preferredMagnitude = magnitudes[event.preferredMagnitudeID()]
        if not preferredMagnitude:
            seiscomp.logging.warning("%s: magnitude %s not found" % (eventID, event.preferredMagnitudeID()))
            # Try to load from memory
            preferredMagnitude = Magnitude.Find(event.preferredMagnitudeID())
        if not preferredMagnitude:
            seiscomp.logging.warning("%s: magnitude %s not found in memory either" % (eventID, event.preferredMagnitudeID()))
            # Load it from database
            preferredMagnitude = loadMagnitude(query, event.preferredMagnitudeID())
        if not preferredMagnitude:
            seiscomp.logging.warning("%s: magnitude %s not found in database either" % (eventID, event.preferredMagnitudeID()))

    # Load focal mechanism, moment tensor, moment magnitude and related origins
    momentTensor = momentMagnitude = derivedOrigin = triggeringOrigin = None
    if event.preferredFocalMechanismID():
        preferredFocalMechanism = focalMechanisms[event.preferredFocalMechanismID()]
        for i in range(preferredFocalMechanism.momentTensorCount()):
            momentTensor = preferredFocalMechanism.momentTensor(i)

        if preferredFocalMechanism.triggeringOriginID():
            if event.preferredOriginID() == preferredFocalMechanism.triggeringOriginID():
                triggeringOrigin = preferredOrigin
            else:
                if preferredFocalMechanism.triggeringOriginID() in origins:
                    triggeringOrigin = origins[preferredFocalMechanism.triggeringOriginID()]
                else:
                    triggeringOrigin = None

                if not triggeringOrigin:
                    seiscomp.logging.warning("triggering origin %s not in origins" % preferredFocalMechanism.triggeringOriginID())
                if not triggeringOrigin:
                    triggeringOrigin = loadOrigin(
                        query, preferredFocalMechanism.triggeringOriginID(), strip=True)
                if not triggeringOrigin:
                    seiscomp.logging.warning("triggering origin %s not in database either" % preferredFocalMechanism.triggeringOriginID())
                    raise RuntimeError()


        if preferredFocalMechanism.momentTensorCount() > 0:
            momentTensor = preferredFocalMechanism.momentTensor(0)
            if momentTensor.derivedOriginID():
                if momentTensor.derivedOriginID() not in origins:
                    seiscomp.logging.warning("momentTensor.derivedOriginID() not in origins")
                    derivedOrigin = loadOrigin(
                        query, momentTensor.derivedOriginID(), strip=True)
                    origins[momentTensor.derivedOriginID()] = derivedOrigin
            if momentTensor.momentMagnitudeID():
                if momentTensor.momentMagnitudeID() == \
                        event.preferredMagnitudeID():
                    momentMagnitude = preferredMagnitude
                else:
                    momentMagnitude = loadMagnitude(
                        query, momentTensor.momentMagnitudeID())

        # Take care of FocalMechanism and related references
        while (event.focalMechanismReferenceCount() > 0):
            event.removeFocalMechanismReference(0)
        if preferredFocalMechanism:
            event.add(FocalMechanismReference(preferredFocalMechanism.publicID()))



    picks = dict()
    ampls = dict()
    if withPicks:
        for originID in origins:
            for pick in query.getPicks(originID):
                pick = Pick.Cast(pick)
                if pick.publicID() not in picks:
                    picks[pick.publicID()] = pick
            for ampl in query.getAmplitudesForOrigin(origin.publicID()):
                ampl = Amplitude.Cast(ampl)
                if ampl.publicID() not in ampls:
                    ampls[ampl.publicID()] = ampl

    # Populate EventParameters instance
    ep.add(event)

    while (event.originReferenceCount() > 0):
        event.removeOriginReference(0)
    for originID in origins:
        event.add(OriginReference(originID))
        ep.add(origins[originID])

    if preferredFocalMechanism:
        if derivedOrigin:
            if momentMagnitude:
                derivedOrigin.add(momentMagnitude)
        ep.add(preferredFocalMechanism)

    for pickID in picks:
        ep.add(picks[pickID])
    for amplID in ampls:
        ep.add(ampls[amplID])

    if not comments:
        scstuff.util.recursivelyRemoveComments(ep)

    return ep


def loadPicksForTimespan(
        query, startTime, endTime,
        withAmplitudes=False,
        authors=None):

    """
    Load from the database all picks within the given time span. If specified,
    also all amplitudes that reference any of these picks may be returned.
    """

    seiscomp.logging.debug("using author whitelist: "+str(authors))
    objects = {}

    # Count objects before filtering
    totalObjectCount = 0

    for obj in query.getPicks(startTime, endTime):
        totalObjectCount += 1
        pick = Pick.Cast(obj)
        if pick:
            if authors:
                try:
                    author = pick.creationInfo().author()
                except ValueError:
                    # ignore pick without author
                    continue
                if author not in authors:
                    continue
            objects[pick.publicID()] = pick

    pickCount = len(objects)
    seiscomp.logging.debug("loaded %d picks" % pickCount)
    seiscomp.logging.debug("loaded %d objects in total" % totalObjectCount)

    if not withAmplitudes:
        return objects
        
    for obj in query.getAmplitudes(startTime, endTime):
        totalObjectCount += 1
        ampl = Amplitude.Cast(obj)
        if ampl:
            if not ampl.pickID():
                continue
            # We don't do any author check here

            if ampl.pickID() not in objects:
                continue

            objects[ampl.publicID()] = ampl

    amplitudeCount = len(objects) - pickCount
    seiscomp.logging.debug("loaded %d amplitudes" % amplitudeCount)
    seiscomp.logging.debug("loaded %d objects in total" % totalObjectCount)

    return objects

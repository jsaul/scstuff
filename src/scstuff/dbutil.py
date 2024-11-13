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


def loadEvent(query, eventID):
    """
    Retrieve event from DB incl. children

    Returns either the event instance
    or None if event could not be loaded.

    Uses loadObject() to also load the children.
    """
    obj = query.loadObject(Event.TypeInfo(), eventID)
    event = Event.Cast(obj)
    if event:
        if event.eventDescriptionCount() == 0:
            query.loadEventDescriptions(event)
        return event


def loadOrigin(query, originID, strip=False):
    """
    Retrieve origin from DB without children

    Returns either the origin instance
    or None if origin could not be loaded.
    """

    # Remark: An Origin can be loaded using loadObject() and
    # getObject(). The difference is that getObject() doesn't
    # load the arrivals hence is a *lot* faster.
    # obj = query.loadObject(Origin.TypeInfo(), originID)
    obj = query.getObject(Origin.TypeInfo(), originID)
    origin = Origin.Cast(obj)
    if origin:
        if strip:
            # OBSOLETE
            scstuff.util.stripOrigin(origin)
        return origin


def loadMagnitude(query, magnitudeID):
    """
    Retrieve magnitude from DB without children

    Returns either the Magnitude instance
    or None if Magnitude could not be loaded.
    """
    obj = query.getObject(Magnitude.TypeInfo(), magnitudeID)
    magnitude = Magnitude.Cast(obj)
    if magnitude:
        return magnitude


def loadFocalMechanism(query, fmid, strip=False):
    """
    Retrieve FocalMechanism from DB without children

    Returns either the FocalMechanism instance
    or None if FocalMechanism could not be loaded.
    """
    # TODO: check
    obj = query.getObject(FocalMechanism.TypeInfo(), fmid)
    focalMechanism = FocalMechanism.Cast(obj)
    if focalMechanism:
        query.loadMomentTensors(focalMechanism)
    return focalMechanism


def getOrigins(query, eventID):
    """
    This is an extended DatabaseQuery.getOrigins(eventID)

    The issue with DatabaseQuery.getOrigins() is that it does not retrieve
    Origin objects for which there is no OriginReference. Origins like that
    are referred to e.g. by FocalMechanism's and MomentTensor's.

    In a second query it also retrieves the FocalMechanism's, loads the
    MomentTensor children and the Origin's referenced from there.
    """
    origins = list()
    for origin in query.getOrigins(eventID):
        origin = Origin.Cast(origin)
        if not origin:
            continue
        origins.append(origin)
        #### UNFINISHED ####
    return origins


def stripCreationInfo(obj):
    # #strip creationInfo entirely:
    # empty = CreationInfo()
    # obj.setCreationInfo(empty)
    obj.creationInfo().setAuthor("")


def stripAuthorInfo(obj):
    try:
        obj.creationInfo().setAuthor("")
    except:
        pass


def stripMomentTensor(mt):
    mt.setGreensFunctionID("")
    while mt.momentTensorStationContributionCount() > 0:
        mt.removeMomentTensorStationContribution(0)
    while mt.momentTensorPhaseSettingCount() > 0:
        mt.removeMomentTensorPhaseSetting(0)


def stripOrigin(origin):
    return scstuff.util.stripOrigin(origin)


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

#   if preferred:
#       preferredOrigin = loadOrigin(query, event.preferredOriginID())
#       if preferredOrigin is None:
#           raise ValueError(
#               "unknown origin '" + event.preferredOriginID() + "'")
#       stripOrigin(preferredOrigin)
#       origins[event.preferredOriginID()] = preferredOrigin
#   else:

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
            seiscomp.logging.debug("%s: triggering origin %s not in origins" % (eventID, triggeringOriginID))
            triggeringOrigin = loadOrigin(query, triggeringOriginID)
            if triggeringOrigin is None:
                seiscomp.logging.warning("%s: failed to load triggering origin %s" % (eventID, triggeringOriginID))
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
    # TODO station magnitudes

    preferredMagnitude = None
    if event.preferredMagnitudeID():
        if event.preferredMagnitudeID() in magnitudes:
            preferredMagnitude = magnitudes[event.preferredMagnitudeID()]
#       for magnitudeID in magnitudes:
#           magnitude = magnitudes[magnitudeID]
#           if magnitude.publicID() == event.preferredMagnitudeID():
#               preferredMagnitude = magnitude
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
#   preferredFocalMechanism = loadFocalMechanism(
#       query, event.preferredFocalMechanismID())
    if event.preferredFocalMechanismID():
        preferredFocalMechanism = focalMechanisms[event.preferredFocalMechanismID()]
#   if preferredFocalMechanism:
        for i in range(preferredFocalMechanism.momentTensorCount()):
            momentTensor = preferredFocalMechanism.momentTensor(i)
            stripMomentTensor(momentTensor)

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

            # TODO: Strip triggering origin if it is not the preferred origin

        if preferredFocalMechanism.momentTensorCount() > 0:
            # FIXME What if there is more than one MT?
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
#       if derivedOrigin:
#           event.add(OriginReference(derivedOrigin.publicID()))
#       if triggeringOrigin:
#           if event.preferredOriginID() != triggeringOrigin.publicID():
#               event.add(OriginReference(triggeringOrigin.publicID()))
        while (event.focalMechanismReferenceCount() > 0):
            event.removeFocalMechanismReference(0)
        if preferredFocalMechanism:
            event.add(FocalMechanismReference(preferredFocalMechanism.publicID()))

    # Strip creation info
    includeFullCreationInfo = True
    if not includeFullCreationInfo:
        stripAuthorInfo(event)

#       if preferredFocalMechanism:
#           stripCreationInfo(preferredFocalMechanism)
#           for i in range(preferredFocalMechanism.momentTensorCount()):
#               stripCreationInfo(preferredFocalMechanism.momentTensor(i))
        for org in [ preferredOrigin, triggeringOrigin, derivedOrigin ]:
            if org is not None:
                stripAuthorInfo(org)
                for i in range(org.magnitudeCount()):
                    stripAuthorInfo(org.magnitude(i))

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
#   if preferredMagnitude and preferredMagnitude is not momentMagnitude:
#       preferredOrigin.add(preferredMagnitude)

    while (event.originReferenceCount() > 0):
        event.removeOriginReference(0)
    for originID in origins:
        event.add(OriginReference(originID))
        ep.add(origins[originID])

    if preferredFocalMechanism:
#       if triggeringOrigin:
#           if triggeringOrigin is not preferredOrigin:
#               ep.add(triggeringOrigin)
        if derivedOrigin:
            if momentMagnitude:
                derivedOrigin.add(momentMagnitude)
#           ep.add(derivedOrigin)
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

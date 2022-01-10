#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-

import sys
import seiscomp.client, seiscomp.datamodel, seiscomp.io
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


def loadOrigin(query, orid, strip=False):
    """
    Retrieve origin from DB without children
    
    Returns either the origin instance
    or None if origin could not be loaded.
    """ 

    # Remark: An Origin can be loaded using loadObject() and
    # getObject(). The difference is that getObject() doesn't
    # load the arrivals hence is a *lot* faster.
    # origin = query.loadObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
    origin = query.getObject(seiscomp.datamodel.Origin.TypeInfo(), orid)
    origin = seiscomp.datamodel.Origin.Cast(origin)
    if origin:
        if strip:
            scstuff.util.stripOrigin(origin)
    return origin


def loadMagnitude(query, orid):
    """
    Retrieve magnitude from DB without children

    Returns either the Magnitude instance
    or None if Magnitude could not be loaded.
    """
    obj = query.getObject(seiscomp.datamodel.Magnitude.TypeInfo(), orid)
    return seiscomp.datamodel.Magnitude.Cast(obj)


def loadFocalMechanism(query, fmid, strip=False):
    """
    Retrieve FocalMechanism from DB without children

    Returns either the FocalMechanism instance
    or None if FocalMechanism could not be loaded.
    """
    # TODO: check
    obj = query.getObject(seiscomp.datamodel.FocalMechanism.TypeInfo(), fmid)
    fm = seiscomp.datamodel.FocalMechanism.Cast(obj)
    if fm:
        query.loadMomentTensors(fm)
    return fm


def stripCreationInfo(obj):
    ## strip creationInfo entirely:
    #empty = seiscomp.datamodel.CreationInfo()
    #obj.setCreationInfo(empty)
    obj.creationInfo().setAuthor("")


def stripMomentTensor(mt):
    mt.setGreensFunctionID("")
    while mt.momentTensorStationContributionCount() > 0:
        mt.removeMomentTensorStationContribution(0)
    while mt.momentTensorPhaseSettingCount() > 0:
        mt.removeMomentTensorPhaseSetting(0)


def loadCompleteEvent(query, eventID, preferredOriginID=None, preferredMagnitudeID=None, preferredFocalMechanismID=None, comments=False, allmagnitudes=False, withPicks=False, preferred=False):
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

    ep = seiscomp.datamodel.EventParameters()

    # Load event and preferred origin. This is the minimum
    # required info and if it can't be loaded, give up.
    event = loadEvent(query, eventID)
    if event is None:
        raise ValueError("unknown event '" + eventID + "'")

    if preferredOriginID:
        event.setPreferredOriginID(preferredOriginID)
    if preferredMagnitudeID:
        event.setPreferredMagnitudeID(preferredMagnitudeID)
    if preferredFocalMechanismID:
        event.setPreferredFocalMechanismID(preferredFocalMechanismID)

    if preferred:
        preferredOrigin = loadOrigin(query, event.preferredOriginID(), strip=True)
        origins = [ preferredOrigin ]
        if preferredOrigin is None:
            raise ValueError("unknown origin '" + event.preferredOriginID() + "'")
    else:
        origins = [ seiscomp.datamodel.Origin.Cast(o) for o in query.getOrigins(eventID) ]

    while (event.originReferenceCount() > 0):
        event.removeOriginReference(0)
    for origin in origins:
        event.add(seiscomp.datamodel.OriginReference(origin.publicID()))
    if comments:
        query.loadComments(preferredOrigin)


    # Load all magnitudes for all loaded origins
    magnitudes = []
    if allmagnitudes:
        for origin in origins:
            query.loadMagnitudes(origin)
            for i in range(origin.magnitudeCount()):
                magnitudes.append(origin.magnitude(i))
    # TODO station magnitudes

    preferredMagnitude = None
    if event.preferredMagnitudeID():
        # first look for magnitude among the magnitude children
        # of the preferred Origin
        for mag in magnitudes:
            if mag.publicID() == event.preferredMagnitudeID():
                preferredMagnitude = mag
                break
        if not preferredMagnitude:
            # try to load from memory
            preferredMagnitude = seiscomp.datamodel.Magnitude.Find(event.preferredMagnitudeID())
        if not preferredMagnitude:
            # load it from database
            preferredMagnitude = loadMagnitude(query, event.preferredMagnitudeID())

    # load focal mechanism, moment tensor, moment magnitude and related origins
    momentTensor = momentMagnitude = derivedOrigin = triggeringOrigin = None
    focalMechanism = loadFocalMechanism(query, event.preferredFocalMechanismID())
    if focalMechanism:
        for i in range(focalMechanism.momentTensorCount()):
            momentTensor = focalMechanism.momentTensor(i)
            stripMomentTensor(momentTensor)

        if focalMechanism.triggeringOriginID():
            if event.preferredOriginID() == focalMechanism.triggeringOriginID():
                triggeringOrigin = preferredOrigin
            else:
                triggeringOrigin = loadOrigin(query, focalMechanism.triggeringOriginID(), strip=True)

        if focalMechanism.momentTensorCount() > 0:
            momentTensor = focalMechanism.momentTensor(0) # FIXME What if there is more than one MT?
            if momentTensor.derivedOriginID():
                derivedOrigin = loadOrigin(query, momentTensor.derivedOriginID(), strip=True)
            if momentTensor.momentMagnitudeID():
                if momentTensor.momentMagnitudeID() == event.preferredMagnitudeID():
                    momentMagnitude = preferredMagnitude
                else:
                    momentMagnitude = loadMagnitude(query, momentTensor.momentMagnitudeID())

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

    # strip creation info
    includeFullCreationInfo = True
    if not includeFullCreationInfo:
        stripCreationInfo(event)
        if focalMechanism:
            stripCreationInfo(focalMechanism)
            for i in range(focalMechanism.momentTensorCount()):
                stripCreationInfo(focalMechanism.momentTensor(i))
        for org in [ preferredOrigin, triggeringOrigin, derivedOrigin ]:
            if org is not None:
                stripCreationInfo(org)
                for i in range(org.magnitudeCount()):
                    stripCreationInfo(org.magnitude(i))

    picks = []
    ampls = []
    if withPicks:
        for origin in origins:
            for pick in query.getPicks(origin.publicID()):
                picks.append(pick)
            for ampl in query.getAmplitudesForOrigin(origin.publicID()):
                ampls.append(ampl)

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

    # count objects before filtering
    totalObjectCount = 0

    for obj in query.getPicks(startTime, endTime):
        totalObjectCount += 1
        pick = seiscomp.datamodel.Pick.Cast(obj)
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
        ampl = seiscomp.datamodel.Amplitude.Cast(obj)
        if ampl:
            if not ampl.pickID():
                continue
            # we don't do any author check here

            if ampl.pickID() not in objects:
                continue
    amplitudeCount = len(objects) - pickCount
    seiscomp.logging.debug("loaded %d amplitudes" % amplitudeCount)
    seiscomp.logging.debug("loaded %d objects in total" % totalObjectCount)

    return objects

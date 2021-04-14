#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#                                                                          #
#    Copyright (C) 2020 by GFZ Potsdam                                     #
#                                                                          #
#    author: Joachim Saul                                                  #
#    email:  saul@gfz-potsdam.de                                           #
#                                                                          #
############################################################################

import seiscomp.client
import seiscomp.datamodel
import seiscomp.logging
import scstuff.util


class EventLoaderApp(seiscomp.client.Application):
    """
    Reads event parameters either
      * from a SeisComP3 database (for a specific event) or
      * from a SeisComP3 XML file (for potentially more than one event)
      
    An EventParameters instance is created to be used by derived classes.
    """

    def __init__(self, argc, argv):
        self.setXmlEnabled(True)
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
        self.setRecordStreamEnabled(False)
        self._xmlFile = None


    def setXmlEnabled(self, enable=True):
        """ To be called from __init__() """
        self._xmlEnabled = enable


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

        return True

    
    def _loadEvent(self, publicID):
        # load an Event object from database
        tp = seiscomp.datamodel.Event
        obj = self.query().loadObject(tp.TypeInfo(), publicID)
        obj = tp.Cast(obj)
        if obj is None:
            seiscomp.logging.error("unknown Event '%s'" % publicID)
        return obj

    def _loadOrigin(self, publicID):
        # load an Origin object from database
        tp = seiscomp.datamodel.Origin
        obj = self.query().loadObject(tp.TypeInfo(), publicID)
        obj = tp.Cast(obj)
        if obj is None:
            seiscomp.logging.error("unknown Origin '%s'" % publicID)
        return obj

    def _readEventParametersFromXML(self):
        # TODO: filter only items related to self._eventID if set
        ep = scstuff.util.readEventParametersFromXML(self._xmlFile)
        if ep is None:
            raise TypeError(self._xmlFile + ": no EventParameters found")
        return ep

    def _readEventParametersFromDatabase(self):
        # load event and preferred origin
        # self._eventID is required to be set
        evt = self._loadEvent(self._eventID)
        if not evt:
            return

        originID = evt.preferredOriginID()
        org = self._loadOrigin(originID)
        if not org:
            return

        pick = {}
        for obj in self.query().getPicks(originID):
            p = seiscomp.datamodel.Pick.Cast(obj)
            key = p.publicID()
            pick[key] = p

        ampl = {}
        for obj in self.query().getAmplitudesForOrigin(originID):
            amp = seiscomp.datamodel.Amplitude.Cast(obj)
            key = amp.publicID()
            ampl[key] = amp

        # create and populate EventParameters instance
        ep = seiscomp.datamodel.EventParameters()
        ep.add(evt)
        ep.add(org)
        for key in pick:
            ep.add(pick[key])
        for key in ampl:
            ep.add(ampl[key])
        return ep
        # TODO: focal mechanisms for completeness


    def readEventParameters(self):
        if self._xmlFile:
            ep = self._readEventParametersFromXML()
        else:
            if not self._eventID:
                seiscomp.logging.error("need to specify an event id to read from database")
                return False
            ep = self._readEventParametersFromDatabase()
        if ep:
            return ep
        return None


#    def run(self):
#        if not self._ep:
#            self._ep = self.readEventParameters()
#        if not self._ep:
#            return False
#        return True

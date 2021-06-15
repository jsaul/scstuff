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

import sys, seiscomp.client, seiscomp.datamodel

class PickClient(seiscomp.client.Application):
    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self,argc,argv)
        self.setMessagingEnabled(True)
        self.setLoggingToStdErr(True)
        self.addMessagingSubscription("PICK")

    def addObject(self, parentID, obj):
        pick = seiscomp.datamodel.Pick.Cast(obj)
        if pick:
            print("new pick %s" % pick.publicID())

app = PickClient(len(sys.argv), sys.argv)
app()

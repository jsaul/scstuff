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

# Dump some moment tensor meta information to text.
#
# Could be invoked in a pipeline like:
#
#  scstuff.xml-dump-with-mt.py --debug -d "$db" -E "$evid" |
#  scstuff.xml-to-mt-creation-info.py
#

import sys
import seiscomp.client, seiscomp.datamodel
import scstuff.util


def meta(fm):
    update = fm.creationInfo().creationTime().toString("%Y-%m-%d %H:%M:%S UTC")
    txt = "Analysis performed "
    txt = txt + "manually" if fm.evaluationMode() == seiscomp.datamodel.MANUAL else "automatically"
    txt = txt + "\n"
    txt = txt + "Last updated " + update + "\n"
    return txt


class MomentTensorInfoDumper(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.xmlInputFile = "-"


    def run(self):
        ep = scstuff.util.readEventParametersFromXML(self.xmlInputFile)
        for i in range(ep.focalMechanismCount()):
            fm = ep.focalMechanism(i)
            txt = meta(fm)
            print(txt)
        del ep
        return True


def main():
    argv = sys.argv
    argc = len(argv)
    app = MomentTensorInfoDumper(argc, argv)
    app()

if __name__ == "__main__":
    main()

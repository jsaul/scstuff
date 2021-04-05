#!/usr/bin/env seiscomp-python
#
# Dump moment tensor information to text.
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  python scxml-to-mt-bulletin.py
#

import sys
import seiscomp.client, seiscomp.datamodel, seiscomp.io
import scstuff.mtutil


class MomentTensorDumper(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.xmlInputFile = "stdin"

    def _readEventParametersFromXML(self):
        ar = seiscomp.io.XMLArchive()
        if self.xmlInputFile == "stdin":
            fname = "-"
        else:
            fname = self.xmlInputFile
        if ar.open(fname) == False:
            raise IOError(self.xmlInputFile + ": unable to open")
        obj = ar.readObject()
        if obj is None:
            raise TypeError(self.xmlInputFile + ": invalid format")
        ep  = seiscomp.datamodel.EventParameters.Cast(obj)
        if ep is None:
            raise TypeError(self.xmlInputFile + ": no eventparameters found")
        return ep

    def run(self):
        ep = self._readEventParametersFromXML()

        for i in range(ep.focalMechanismCount()):
            fm = ep.focalMechanism(i)
            txt = scstuff.mtutil.fm2txt(fm)
            print(txt)

        del ep
        return True


def main(argc, argv):
    app = MomentTensorDumper(argc, argv)
    app()

if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)
    main(argc, argv)

#!/bin/sh

evid="gfz2015ncme"
seiscomp-python scstuff.set-magtype.py -H geofon-proc -u "" --event $evid --magnitude-type Mw


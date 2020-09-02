#!/bin/sh

debug=--debug
#debug=

date
~/seiscomp/bin/seiscomp exec seiscomp-python \
    eventclient.py $debug  -u eventwatch -H geofon-proc 2>&1 | tee log.txt
date

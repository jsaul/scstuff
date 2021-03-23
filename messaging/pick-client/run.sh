#!/bin/sh

exec ~/seiscomp/bin/seiscomp exec seiscomp-python \
    pickclient.py -u xyzabc -H geofon-proc --debug

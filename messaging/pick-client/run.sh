#!/bin/sh

# The host to connect to and receive the messages from
host="geofon-proc"

exec ~/seiscomp/bin/seiscomp exec seiscomp-python \
    pick-client.py -u xyzabc -H "$host" --debug

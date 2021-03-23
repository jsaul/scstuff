#!/bin/sh

# Simple SeisComP Python script to demonstrate how to send picks
# read from a pipe. We don't have a real online picker here to play
# with, of course; that's why this demo comes with a dummy picker
# script that simply dumps to standard output what in real life
# would be a pick possibly generated from data or read from a file.
#
# To see what the dummypicker.sh script does, just run it from a
# shell.

# This is the host to send the messages to.
host=geofon-proc

# Comment this out to actually send the pick. However, you certainly
# don't want to do with the dummy picker unless the target messaging
# target is only a test setup.
test=--test

./dummypicker.sh |
~/seiscomp/bin/seiscomp exec seiscomp-python \
    picksender.py $test --debug -H $host

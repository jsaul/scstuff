#!/bin/sh

d=$HOME/log/notifiers
p=$d/notifier-log
mkdir -p $d

$HOME/seiscomp/bin/seiscomp exec ./notifier-logger.py -H geofon-proc.gfz-potsdam.de -u ntflog2 --debug --prefix=$p

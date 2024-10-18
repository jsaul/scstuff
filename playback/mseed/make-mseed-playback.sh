#!/bin/sh

debug=--debug

for evid in "$@"
do
    ./make-mseed-playback.py --event "$evid" $debug 2>&1 |
    tee $evid.log
    scxmldump --inventory --formatted -o $evid-inventory.xml $debug
done

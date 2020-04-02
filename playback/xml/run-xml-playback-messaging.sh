#!/bin/sh

###### configuration #######
# Give name of target host
target_host=st127.gfz-potsdam.de
############################


for evt in "$@"
do
    ~/seiscomp/bin/seiscomp exec seiscomp-python \
        sc3stuff.playback-run-messaging.py \
          --xml "playbacks/$evt/objects.xml" \
          --speed 1 \
          --host $target_host \
          --user "" \
          --debug
done

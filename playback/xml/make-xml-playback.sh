#!/bin/sh -ex

evt="$1" comment="$2"

###### configuration #######
# Specify database in $HOME/.seiscomp/global.cfg, e.g. as
#
#   database = mysql://sysop:sysop@localhost/seiscomp
#
# comment this out in order to suppress debug output
debug=--debug
#
# specify playback target directory (where the playback data
# shall be written to)
playback_d=$HOME/.seiscomp/playbacks
#
############################

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

timewindow="--event $evt --before=3600 --after=7200"

mkdir -p config
for f in grid.conf station.conf
do
    test -f config/$f || cp -p ~/seiscomp/share/scautoloc/$f config/
done

mkdir -p "$playback_d/$evt"
~/seiscomp/bin/seiscomp exec seiscomp-python \
    scstuff.playback-dump-picks.py $timewindow $debug \
    > "$playback_d/$evt"/objects.xml

test -z "$comment" || echo "$evt  $comment" \
    > "$playback_d/$evt"/comment.txt

~/seiscomp/bin/seiscomp exec seiscomp-python \
    scstuff.playback-dump-stations.py $debug \
    > "$playback_d/$evt"/station-locations.txt

~/seiscomp/bin/seiscomp exec \
    scbulletin $debug -3 -E "$evt" \
    > "$playback_d/$evt"/bulletin

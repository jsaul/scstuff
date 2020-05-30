#!/bin/sh -ex

evt="$1" comment="$2"

###### configuration #######
# Give address of database
db="mysql://sysop:sysop@geofon-proc.gfz-potsdam.de/seiscomp3"
#db="mysql://sysop:sysop@geofon-proc2.gfz-potsdam.de/seiscomp3_archive"
#
# comment this out in order to suppress debug output
debug=--debug
#
# specify playback target directory (where the playback data
# shall be written to)
playback_d=$HOME/.seiscomp/playbacks
############################

if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

timewindow="--event $evt --before=86400 --after=86400"

mkdir -p config
for f in grid.conf station.conf
do
    test -f config/$f || cp -p ~/seiscomp/share/scautoloc/$f config/
done

mkdir -p "$playback_d/$evt"
~/seiscomp/bin/seiscomp exec seiscomp-python \
    scstuff.playback-dump-picks.py $timewindow $debug -d "$db" \
    > "$playback_d/$evt"/objects.xml

test -z "$comment" || echo "$evt  $comment" \
    > "$playback_d/$evt"/comment.txt

~/seiscomp/bin/seiscomp exec seiscomp-python \
    scstuff.playback-dump-stations.py $debug -d "$db" \
    > "$playback_d/$evt"/station-locations.txt

~/seiscomp/bin/seiscomp exec \
    scbulletin $debug -3 -d "$db" -E "$evt" \
    > "$playback_d/$evt"/bulletin

#!/bin/sh -ex

evt="$1"

###### configuration #######
# specify playback directory (where the playback data
# were written to)
playback_d=$HOME/.seiscomp/playbacks
#
# comment this out in order to suppress debug output
debug=--debug
############################

export PATH=$PATH:.
export LC_ALL=C


if test -z "$evt"
then
    echo "specify event ID"
    exit 1
fi

strip_time () {
    sed 's/[0-9][0-9]:[0-9][0-9]:[0-9][0-9] \[/[/'
}


case "$evt" in
gfz*)
    descr="$playback_d/$evt/description.txt"
    test -f "$descr" || wget -O "$descr" "http://geofon.gfz-potsdam.de/eqinfo/event.php?id=$evt&fmt=txt" >/dev/null 2>&1
    ( cat "$descr"; echo ) >&2
    ;;
esac

xml="$playback_d/$evt/objects.xml"

#valgrind --track-origins=yes -v \
~/seiscomp/bin/seiscomp exec \
scautoloc -v --console=1 $debug \
    --use-manual-origins 1 \
    --offline --playback --input "$xml" --speed 0 \
    --station-locations   $playback_d/$evt/station-locations.txt \
    --station-config      config/station.conf \
    --grid                config/grid.conf \
    2>&1 |
strip_time | tee $evt-playback.log

grep OUT $evt-playback.log


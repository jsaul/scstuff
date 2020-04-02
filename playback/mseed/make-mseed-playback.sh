#!/bin/sh

###### configuration #######
# Give name of processing host
host="geofon-proc"
# Give name of config file. Make sure you
# adopt it to your needs!
cfg="acqui.cfg"
# location of your database
db="mysql://sysop:sysop@$host/seiscomp3"
############################

# specify event id(s) on the command line

scexec="$HOME/seiscomp/bin/seiscomp exec"

for evid in "$@"
do
    $scexec ./make-mseed-playback.py --event "$evid" --config-file "$cfg" --database "$db"  --debug 2>&1 |
    tee $evid.log
    $scexec scxmldump --inventory --formatted -o $evid-inventory.xml --database "$db" --debug
done


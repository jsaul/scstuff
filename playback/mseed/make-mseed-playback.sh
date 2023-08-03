#!/bin/sh

###### configuration #######
# Specify database in $HOME/.seiscomp/global.cfg, e.g. as
#
#   database = mysql://sysop:sysop@localhost/seiscomp
#
# comment this out in order to suppress debug output
# comment this out in order to suppress debug output
debug=--debug
#
# specify playback target directory (where the playback data
# shall be written to)
playback_d=$HOME/.seiscomp/playbacks
#
############################

# specify event id(s) on the command line

scexec="$HOME/seiscomp/bin/seiscomp exec"

for evid in "$@"
do
    $scexec ./make-mseed-playback.py --event "$evid" $debug 2>&1 |
    tee $evid.log
    $scexec scxmldump --inventory --formatted -o $evid-inventory.xml $debug
done


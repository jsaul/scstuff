#!/bin/sh

while true
do
    for sta in ABC CDE EFG GHI
    do
        date +"Pick#%Y%m%dT%H%M%S#test %Y-%m-%dT%H:%M:%S.123Z XY $sta"
        sleep 1
    done
done

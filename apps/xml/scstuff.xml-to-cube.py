#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (C) GFZ Potsdam                                               #
# All rights reserved.                                                    #
#                                                                         #
# Author: Joachim Saul (saul@gfz-potsdam.de)                              #
#                                                                         #
# GNU Affero General Public License Usage                                 #
# This file may be used under the terms of the GNU Affero                 #
# Public License version 3.0 as published by the Free Software Foundation #
# and appearing in the file LICENSE included in the packaging of this     #
# file. Please review the following information to ensure the GNU Affero  #
# Public License version 3.0 requirements will be met:                    #
# https://www.gnu.org/licenses/agpl-3.0.html.                             #
###########################################################################
#
# Dump event information to the so-called "CUBE" format.
#
# Could be invoked in a pipeline like:
#
# scstuff.xml-to-cube.py --debug -d "$db" -E "$evid" | mail -s ...

import sys, optparse
import scstuff.util
import seiscomp.datamodel

networkCode = "GE"

def MenloCheckChar(pch):
    """
    int MenloCheckChar( char* pch )
    {
        unsigned short sum;

        for( sum=0; *pch; pch++ )
            sum = ((sum&01)?0x8000:0) + (sum>>1) + *pch;

        return (int)(36+sum%91);
    }
    """ 
    assert len(pch) == 79
    s = 0
    for c in pch:
        if ((s & 1) != 0):
            s = (s >> 1) + 0x8000;
        else:
            s >>= 1;

        c = ord(c)
        s += c
        s &= 0xFFFF;
    return chr(36+s%91)

t = "E 09082344CI21999040217051050339860-1169945017316000014001800120009004332C0002h"
assert MenloCheckChar(t) == "P"
t = "E meav    US3199904021838195-201884 1681247 33054 19 192283 062 387  00  B 8   "
assert MenloCheckChar(t) == "v"

def cube(ep):
    """
    a2 * Tp   = Message type = "E " (seismic event)
    a8 * Eid  = Event identification number  (any string)
    a2 * So   = Data Source =  regional network designation
    a1 * V    = Event Version     (ASCII char, except [,])
    i4 * Year = Calendar year                (GMT) (-999-6070)
    i2 * Mo   = Month of the year            (GMT) (1-12)
    i2 * Dy   = Day of the month             (GMT) (1-31)
    i2 * Hr   = Hours since midnight         (GMT) (0-23)
    i2 * Mn   = Minutes past the hour        (GMT) (0-59)
    i3 * Sec  = Seconds past the minute * 10 (GMT) (0-599)
    i7 * Lat  = Latitude:  signed decimal degrees*10000 north>0
    i8 * Long = Longitude: signed decimal degrees*10000 west <0
    i4   Dept = Depth below sea level, kilometers * 10
    i2   Mg   = Magnitude * 10
    i3   Nst  = Number of stations used for location
    i3   Nph  = Number of phases used for location
    i4   Dmin = Distance to 1st station;   kilometers * 10
    i4   Rmss = Rms time error; sec * 100
    i4   Erho = Horizontal standard error; kilometers * 10
    i4   Erzz = Vertical standard error;   kilometers * 10
    i2   Gp   = Azimuthal gap, percent of circle; degrees/3.6
    a1   M    = Magnitude type
    i2   Nm   = Number of stations for magnitude determination
    i2   Em   = Standard error of the magnitude * 10
    a1   L    = Location method
    a1 * C    = Menlo Park check character, defined below
    """

    evt = ep.event(0)
    eventID = evt.publicID()
    org = scstuff.util.ep_get_origin(ep, eventID, evt.preferredOriginID())
    mag = scstuff.util.ep_get_magnitude(ep, eventID)

    msg = "E "
    msg += eventID[-8:]
    msg += (networkCode+"  ")[:2]
    eventVersion = "A"
    msg += eventVersion[:1]
    msg += org.time().value().toString("%Y%m%d%H%M%S%f")[:15]
    msg += "%+07d" % int(org.latitude().value()*10000)
    msg += "%+08d" % int(org.longitude().value()*10000)
    msg += "%4d"   % int(org.depth().value()*10)
    msg += "%2d"   % int(mag.magnitude().value()*10+0.5)
    nst = org.quality().usedStationCount()
    nph = org.quality().usedPhaseCount()
    msg += "%3d%3d" % (nst, nph)
    dmin = org.quality().minimumDistance()
    dmin = min(int(dmin * 111.195 * 10), 9999)
    msg += "%4d" % dmin
    rmss = int(org.quality().standardError() * 100)
    msg += "%4d" % rmss
    try:
        xerr = org.uncertainty().maxHorizontalUncertainty()
    except ValueError:
        xerr = 0
    msg += "%4d" % int(xerr*10)
    try:
        zerr = org.depth().uncertainty()
    except ValueError:
        zerr = 0
    msg += "%4d" % int(zerr*10)
    msg += "%2d" % int(org.quality().azimuthalGap()/3.6)

    # By default we assume body-wave magnitude
    mtype = "B"
    # If it's any of the Mw* incl. Mw proxies, then moment magnitude
    if mag.type().startswith("Mw"):
        mtype = "O"
    msg += mtype
    msg += "%2d" % min(mag.stationCount(), 99)
    try:
        merr = mag.magnitude().uncertainty()
    except ValueError:
        if mag.type() == "Mw":
            merr = 0.15
        else:
            merr = 0.3
    msg += "%2d" % int(merr*10+0.5)
    msg += "F"

    return msg + MenloCheckChar(msg)


def summary(ep):
    evt = ep.event(0)
    eventID = evt.publicID()
    org = scstuff.util.ep_get_origin(ep, eventID, evt.preferredOriginID())
    mag = scstuff.util.ep_get_magnitude(ep, eventID)

    for i in range(evt.eventDescriptionCount()):
        evtd = evt.eventDescription(i)
        evtdtype = seiscomp.datamodel.EEventDescriptionTypeNames.name(
            evtd.type())
        if evtdtype == "region name":
            region = evtd.text()

    msg  = "Event ID        %s\n" % eventID
    if region:
        msg += "Region          %s\n" % region
    msg += "Origin Time     %s\n" % (org.time().value().toString("%Y-%m-%d %H:%M:%S"))
    msg += "Latitude      %+8.3f\n" % org.latitude().value()
    msg += "Longitude     %+8.3f\n" % org.longitude().value()
    msg += "Depth         %4d km\n" % int(org.depth().value()+0.5)
    msg += "Magnitude      %6.2f\n" % mag.magnitude().value()
    return msg

description="%prog - dump moment tensor information from XML files to text"

p = optparse.OptionParser(usage="%prog filename[s] >", description=description)
p.add_option("-E", "--event", help="specify event ID")
p.add_option("-v", "--verbose", action="store_true", help="run in verbose mode")

(opt, filenames) = p.parse_args()

if not filenames:
    filenames = [ "-" ]

for filename in filenames:
    ep = scstuff.util.readEventParametersFromXML(filename)
    print(cube(ep))
    if opt.verbose:
        print()
        print(summary(ep))
    del ep

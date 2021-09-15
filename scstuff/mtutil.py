from math import sin, cos, log10, sqrt, atan2, pi
import seiscomp.datamodel
import seiscomp.seismology

def radiationPattern(Mxx, Myy, Mzz, Mxy, Mxz, Myz, azi, inc):
    """
    Compute radiation pattern as (P,SV,SH) amplitude tuple.
    # Parameters:
    #   Moment tensor elements
    #   azimuth, incidence angle in degrees
    #
    # Returns:
    #   P, SV, SH radiation patterns
    """

    # For the angles see Pujol (9.9.16) etc.  phi==azi theta==inc

    cosazi = cos(azi*pi/180)
    sinazi = sin(azi*pi/180)
    cosinc = cos(inc*pi/180)
    sininc = sin(inc*pi/180)

    # Gamma, Theta, Phi are unit vectors:
    #
    # Gamma points away from the source (P direction)
    # Theta points in the direction of increasing incidence angle (SV plane)
    # Phi points in the direction of increasing azimuth (SH plane)
    #
    # See Pujol fig. 9.10

    Gamma_x  =  sininc*cosazi
    Gamma_y  =  sininc*sinazi
    Gamma_z  =  cosinc

    Theta_x  =  cosinc*cosazi
    Theta_y  =  cosinc*sinazi
    Theta_z  = -sininc

    Phi_x  = -sinazi
    Phi_y  =  cosazi
    Phi_z  =  0

    M_Gamma_x = Mxx*Gamma_x + Mxy*Gamma_y + Mxz*Gamma_z
    M_Gamma_y = Mxy*Gamma_x + Myy*Gamma_y + Myz*Gamma_z
    M_Gamma_z = Mxz*Gamma_x + Myz*Gamma_y + Mzz*Gamma_z

    P  = Gamma_x*M_Gamma_x + Gamma_y*M_Gamma_y + Gamma_z*M_Gamma_z
    SV = Theta_x*M_Gamma_x + Theta_y*M_Gamma_y + Theta_z*M_Gamma_z
    SH =   Phi_x*M_Gamma_x +   Phi_y*M_Gamma_y +   Phi_z*M_Gamma_z

    return P, SV, SH


def renderTensor(Mxx, Myy, Mzz, Mxy, Mxz, Myz, nx=33, ny=19):
    """
    Renders the tensor as textual beachball graphics with nx columns
    and ny rows.

    Returns a text string.

    The default dimension 33x19 is like in the GEOFON MT bulletin emails.
    """
    txt = ""
    for iy in range(ny):
        y = 2.*((ny-iy-0.5)-ny/2)/ny
        line = ""
        for ix in range(nx):
            x = 2.*((ix+0.5)-nx/2)/nx
            r = sqrt(x**2+y**2)
            if r>1:
                line += " "
                continue
            azi = atan2(x,y)*180/pi
            inc = r*90
            rp,rsv,rsh = radiationPattern(Mxx, Myy, Mzz, Mxy, Mxz, Myz, azi, inc)
            if rp > 0:
                line += "#"
            else:
                line += "-"
        txt += "%s\n" % line
    return txt


def fm2txt(fm):
    """
    Generate "bulletin" style output for a given focal mechanism.
    This is the format also used on the GFZ/GEOFON webpages. It is
    used for human consumption only. Don't use this format for data
    exchange as there is absolutely no guarantee that this format
    will stay as it is. Repeat: DON'T use it for data exchange!

    This function assumes that all objects can be accessed via
    the PublicObject registry.
    """

    try:
        np_str =  fm.nodalPlanes().nodalPlane1().strike()
        np_dip =  fm.nodalPlanes().nodalPlane1().dip()
        np_rake = fm.nodalPlanes().nodalPlane1().rake()
    except:
        seiscomp.logging.error("Cannot determine nodal planes")
        return

    if fm.momentTensorCount() == 0:
        seiscomp.logging.error("FocalMechanism without MomentTensor")
        return 

    mt = fm.momentTensor(0)
    mag = seiscomp.datamodel.Magnitude.Find(mt.momentMagnitudeID())
    if not mag:
        seiscomp.logging.error("Magnitude %s not found", mt.momentMagnitudeID())
        return

    triggeringOrigin = seiscomp.datamodel.Origin.Find(fm.triggeringOriginID())
    if not triggeringOrigin:
        seiscomp.logging.error("Triggering origin %s not found", fm.triggeringOriginID())
        return

    derivedOrigin = seiscomp.datamodel.Origin.Find(mt.derivedOriginID())
    if not derivedOrigin:
        seiscomp.logging.error("Derived origin %s not found", mt.derivedOriginID())
        return

    isCentroid = False
    try:
        if derivedOrigin.type() == seiscomp.datamodel.CENTROID:
            isCentroid = True
    except:
        pass

    tim = triggeringOrigin.time().value().toString("%y/%m/%d %H:%M:%S.%2f")
    lat = triggeringOrigin.latitude().value()
    lon = triggeringOrigin.longitude().value()
    regionName = seiscomp.seismology.Regions.getRegionName(lat, lon)
    mw = mag.magnitude().value()
    try:
        agencyID = m.creationInfo().agencyID()
    except:
        agencyID = "GFZ" # FIXME

    lines = []
    lines.append(tim)
    lines.append(regionName)
    lines.append("Epicenter: %.2f %.2f" % (lat, lon))
    lines.append("MW %.1f" % (mw))
    lines.append("")

    if isCentroid:
        lines.append("%s CENTROID MOMENT TENSOR SOLUTION" % agencyID)
        tim = derivedOrigin.time().value().toString("%y/%m/%d %H:%M:%S.%2f")
        lat = derivedOrigin.latitude().value()
        lon = derivedOrigin.longitude().value()
        lines.append("Centroid:  %.2f %.2f" % (lat, lon))
        lines.append(tim)
    else:
        lines.append("%s MOMENT TENSOR SOLUTION" % agencyID)

    depth = int(derivedOrigin.depth().value()+0.5)
    try:
        stationCount = derivedOrigin.quality().usedStationCount()
    except ValueError:
        # for some legacy events at GFZ we have to use this fallback
        try:
            stationCount = derivedOrigin.magnitude(0).stationCount()
        except ValueError:
            stationCount = -1
    lines.append("Depth %3d  %21s" % (depth, ("No. of sta: %d" % stationCount)))

    expo = 0
    tensor = mt.tensor()
    Mrr = tensor.Mrr().value()
    Mtt = tensor.Mtt().value()
    Mpp = tensor.Mpp().value()
    Mrt = tensor.Mrt().value()
    Mrp = tensor.Mrp().value()
    Mtp = tensor.Mtp().value()
    expo = max(expo, log10(abs(Mrr)))
    expo = max(expo, log10(abs(Mtt)))
    expo = max(expo, log10(abs(Mpp)))
    expo = max(expo, log10(abs(Mrt)))
    expo = max(expo, log10(abs(Mrp)))
    expo = max(expo, log10(abs(Mtp)))

    Tval = fm.principalAxes().tAxis().length().value()
    Nval = fm.principalAxes().nAxis().length().value()
    Pval = fm.principalAxes().pAxis().length().value()

    expo = max(expo, log10(abs(Tval)))
    expo = max(expo, log10(abs(Nval)))
    expo = max(expo, log10(abs(Pval)))
    expo = int(expo)

    Tdip = fm.principalAxes().tAxis().plunge().value()
    Tstr = fm.principalAxes().tAxis().azimuth().value()
    Ndip = fm.principalAxes().nAxis().plunge().value()
    Nstr = fm.principalAxes().nAxis().azimuth().value()
    Pdip = fm.principalAxes().pAxis().plunge().value()
    Pstr = fm.principalAxes().pAxis().azimuth().value()

    lines.append("Moment Tensor;   Scale 10**%d Nm" % expo)
    q = 10**expo
    lines.append("  Mrr=%5.2f       Mtt=%5.2f" % (Mrr/q, Mtt/q))
    lines.append("  Mpp=%5.2f       Mrt=%5.2f" % (Mpp/q, Mrt/q))
    lines.append("  Mrp=%5.2f       Mtp=%5.2f" % (Mrp/q, Mtp/q))

    lines.append("Principal axes:")
    lines.append("  T  Val= %5.2f  Plg=%2d  Azm=%3d" % (Tval/q, Tdip, Tstr))
    lines.append("  N       %5.2f      %2d      %3d" % (Nval/q, Ndip, Nstr))
    lines.append("  P       %5.2f      %2d      %3d" % (Pval/q, Pdip, Pstr))

    lines.append("")
    moment = mt.scalarMoment().value()
    expo = int(log10(moment))
    moment *= 10**-expo
    np1 = fm.nodalPlanes().nodalPlane1();
    np2 = fm.nodalPlanes().nodalPlane2();
    s1, d1, r1 = np1.strike().value(), np1.dip().value(), np1.rake().value()
    s2, d2, r2 = np2.strike().value(), np2.dip().value(), np2.rake().value()
    lines.append("Best Double Couple:Mo=%3.1f*10**%d" % (moment, expo))
    lines.append(" NP1:Strike=%3d Dip=%2d Slip=%4d" % (s1, d1, r1))
    lines.append(" NP2:       %3d     %2d      %4d" % (s2, d2, r2))

    Mxx, Myy, Mzz, Mxy, Mxz, Myz = Mtt, Mpp, Mrr, -Mtp, Mrt, -Mrp
    txt = renderTensor(Mxx, Myy, Mzz, Mxy, Mxz, Myz)
    lines.append(txt)

    txt = "\n".join(lines)
    return txt

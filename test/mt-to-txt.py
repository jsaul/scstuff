import seiscomp.datamodel
import scstuff.util
import scstuff.mtutil

def test_mttxt(verbose=False):
    filename = "Data/event.xml"
    ep = scstuff.util.readEventParametersFromXML(filename)
    assert seiscomp.datamodel.PublicObject.ObjectCount() == 14
    assert ep.focalMechanismCount() == 1
    fm = ep.focalMechanism(0)
    txt = scstuff.mtutil.fm2txt(fm)
    if verbose:
        print(txt)
    assert len(txt) == 1122
    del ep
    assert seiscomp.datamodel.PublicObject.ObjectCount() == 0

if __name__ == "__main__":
    verbose = True
    test_mttxt(verbose)

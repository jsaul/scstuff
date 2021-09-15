import seiscomp.datamodel
import scstuff.util
import scstuff.mtutil


expected = """21/04/03 01:16:40.08
East of South Sandwich Islands
Epicenter: -58.05 -7.88
MW 6.6

GFZ MOMENT TENSOR SOLUTION
Depth  18          No. of sta: 0
Moment Tensor;   Scale 10**19 Nm
  Mrr=-0.15       Mtt=-0.55
  Mpp= 0.71       Mrt= 0.07
  Mrp= 0.08       Mtp= 0.76
Principal axes:
  T  Val=  1.08  Plg= 4  Azm=295
  N       -0.16      84       85
  P       -0.92       2      205

Best Double Couple:Mo=1.0*10**19
 NP1:Strike=340 Dip=84 Slip= 178
 NP2:        70     88         5
           #----------           
        ####-------------        
     ########---------------     
    ##########---------------    
  ############-----------------  
  ############-----------------  
 ##############---------------## 
##############-------------######
##############----------#########
#############---------###########
###########----------############
########------------#############
 ###----------------############ 
  ------------------###########  
  ------------------###########  
    -----------------########    
     ----------------#######     
        -------------####        
           ----------#           
"""


expected2 = """11/01/26 08:01:30.02
Eastern New Guinea Reg., P.N.G.
Epicenter: -5.47 147.12
MW 5.4

GFZ MOMENT TENSOR SOLUTION
Depth 216         No. of sta: 19
Moment Tensor;   Scale 10**16 Nm
  Mrr= 8.00       Mtt=-5.23
  Mpp=-2.77       Mrt= 1.15
  Mrp=-2.24       Mtp=-5.23
Principal axes:
  T  Val=  8.44  Plg=79  Azm= 88
  N        1.31       8      310
  P       -9.75       7      219

Best Double Couple:Mo=9.2*10**16
 NP1:Strike=137 Dip=53 Slip= 100
 NP2:       300     38        77
           -----------           
        ----------------#        
     ---------------########     
    -------------############    
  -------------################  
  -----------##################  
 ----------##################### 
----------######################-
---------#####################---
--------#####################----
-------#####################-----
------####################-------
 ----###################-------- 
  ##################-----------  
  ##############---------------  
    #####--------------------    
     ###--------------------     
        -----------------        
           -----------           
"""


def test_mttxt(verbose=False):
    """
    Tests the proper generation of MT text format.

    Note that this format is on no way static and may change
    in the future.
    """
    filename = "Data/event.xml"
    ep = scstuff.util.readEventParametersFromXML(filename)
    assert seiscomp.datamodel.PublicObject.ObjectCount() == 14
    assert ep.focalMechanismCount() == 1
    fm = ep.focalMechanism(0)
    txt = scstuff.mtutil.fm2txt(fm)
    if verbose:
        print(txt)
    assert len(txt) == 1122
    assert txt == expected
    del ep
    assert seiscomp.datamodel.PublicObject.ObjectCount() == 0

def test_mttxt_legacy_event(verbose=False):
    """
    Test for a GFZ legacy event XML file with missing Origin.quality.
    """
    filename = "Data/event2.xml"
    ep = scstuff.util.readEventParametersFromXML(filename)
    print(seiscomp.datamodel.PublicObject.ObjectCount())
    assert ep.focalMechanismCount() == 1
    fm = ep.focalMechanism(0)
    txt = scstuff.mtutil.fm2txt(fm)
    if verbose:
        print(txt)
    assert len(txt) == 1123
    assert txt == expected2
    del ep
    assert seiscomp.datamodel.PublicObject.ObjectCount() == 0

if __name__ == "__main__":
    verbose = True
    test_mttxt(verbose)
    test_mttxt_legacy_event(verbose)

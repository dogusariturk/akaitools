c--------------------NiFe------------------------------------
     spc   data/nife
c------------------------------------------------------------
c   brvtyp     a        c/a   b/a   alpha   beta   gamma
     fcc      6.55  ,      ,      ,      ,       ,      ,
c------------------------------------------------------------
c   edelt    ewidth    reltyp   sdftyp   magtyp   record
    0.001     1.0       nrl      mjw      mag      2nd
c------------------------------------------------------------
c   outtyp    bzqlty   maxitr   pmix
    update      20        100    0.03tch
c------------------------------------------------------------
c    ntyp
      1
c------------------------------------------------------------
c   type    ncmp    rmt    field   mxl  anclr   conc
    NiFe     2       1      0.0     2
                                          28     50
                                          26     50
c------------------------------------------------------------
c   natm
     1
c------------------------------------------------------------
c   atmicx                        atmtyp
     0          0          0        NiFe
c------------------------------------------------------------
#end
# number of k-point along symmetry line
 300
# For fcc bravais lattice, the dispersion relation along
# W-L-G-X-W-K symmetry points (below) is usually calculated.
 1 1/2 0
 1/2 1/2 1/2
 0 0 0
 1 0 0
 1 1/2 0
 3/4 3/4 0

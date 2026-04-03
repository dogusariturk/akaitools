c----------------------Fe------------------------------------
    spc   data/fe
c------------------------------------------------------------
c   brvtyp     a        c/a   b/a   alpha   beta   gamma
    bcc        5.27  ,        ,      ,      ,       ,      ,
c------------------------------------------------------------
c   edelt    ewidth    reltyp   sdftyp   magtyp   record
    0.001     1.0       nrl    mjwasa   mag      2nd
c------------------------------------------------------------
c   outtyp    bzqlty   maxitr   pmix
    update     20        100   0.035
c------------------------------------------------------------
c    ntyp
     1
c------------------------------------------------------------
c   type    ncmp    rmt    field   mxl  anclr   conc
    Fe       1       0      0.0     2     26    100
c------------------------------------------------------------
c   natm
     1
c------------------------------------------------------------
c   atmicx(in the unit of a)     atmtyp
     0         0          0        Fe
c
c------ The following types of inputs and their combination
c       are also allowed.
c------ In those cases a, b, b mean primitive unit vectors
c       and x, y, z mean conventionnal cell vectors along
c       x, y, and z axses. Bare numbers indicate cartesian
c       coordinate in the unit of lattice constant a.
c    1/2       1/2        1/2      Fe
c    0a        0b         0c       Fe
c    0x        0y         0z       Fe
c    1/2a      1/2b       1/2c     Fe
c------------------------------------------------------------
c  "end" means the end of input data
c  "end" is not necessary unless other data used only
c   for "spc" exist below.
c----------------------Fe------------------------------------
 end
# The following data are used in the 'spc' mode.
# number of k-point along symmetry line
 300
# For bcc bravais lattice, the dispersion relation along
# G-H-N-P-G-N symmetry points (below) is usually calculated.
 0 0 0
 0 1 0
 1/2 1/2 0
 1/2 1/2 1/2
 0 0 0
 1/2 1/2 0

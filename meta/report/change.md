
# Remarks

Ce document contient les changements que j'aurais fais vers Rubicon Suite et leur justification

This document contains the different changing from the actual version.

## Database

* metal Cost/Ounce -> metal cost/kg 
    bien que la ounce employe est surement celle de Troy (31,1034768 g), employé une unité de mesure dont 
    on n'est même pas sure de la définition est source d'erreure.


* Stone density 
    Before the density is relative to the quartz used as a reference. Now we prefere having the real density in g/cm3. (Quartz ~2.65g/cm3 +- 0.005)
    
Not sure yet     
* Product/Model -> Product/Template 
    This change come from the fact that Model is used in a technical way to describe a table (Model/View)


* DEL ProductCatagories  
    This table was only used by Products and in Products, all the fields were one `1` wich means all. So this table is useless.
    
* DEL Grades 
    Used only in the StoneLots table, only the grade A is used and appeared on PDP only on `Stone Cost Chart`.


* MiscType (laser, plating, ...) -> Addon (more explicit word)

* Labor (LAB) -> Assembly (ASS)





## Standards 

### Model

AAXXXXB : 
* AA : Category 
* XXXX : Model id 
* B (opt): Model variation

### Stone Composition
S+A.S1+S2
* Si : stone
* A (opt) : color

### Product
AAXXXXB-STONES/M :
* AAXXXXB : Model code
* STONES : stone composition code

## Margin | Labor 

### Margin Labor :
* Parts
* Metal Labor
* Stone Labor
* Addon Labor
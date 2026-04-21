@startuml
'---------------------------------------
' Diagramme 5 : Métaux et tarification
'---------------------------------------

' -- Tables principales --

class Metals {
  + MetalID      : char(2)
  + MetalName    : varchar(50)
  + MetalUCost   : decimal(18,0)
  + MetalUCostCurrID : char(2)
  + ApplyPlating : bit
}

class MetalPurities {
  + Purity     : char(5)
  + PurityPer  : decimal(10,0)
}

class MetalConv {
  + MetalID      : char(2)
  + MetalID2     : char(2)
  + ConvPer      : decimal(18,0)
}

class MetalPurityConv {
  + Purity       : char(5)
  + Purity2      : char(5)
  + ConvPer      : decimal(18,0)
}

' -- Schéma des relations de clés étrangères --

MetalPurities     <|-- MetalPurityConv   : Purity\nPurity2
Metals            <|-- MetalConv         : MetalID\nMetalID2

@enduml

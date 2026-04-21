@startuml pdp_alloy
               
  skinparam linetype ortho
  skinparam classBackgroundColor #FAFAFA                                                                                                      
  skinparam classBorderColor #888                                                                                                             
  skinparam arrowColor #555                                                                                                                   
  skinparam packageBackgroundColor #F0F4FF                                                                                                    
  skinparam packageBorderColor #99AACC                                                                                                        
   
                                        
                                                            
    class "pdp.raw.metal" as RawMetal {                                                                                                       
      + code : Char [required, unique]                      
      + name : Char [required]                                                                                                                
      + density : Float  [g/cm³]
      + price : Monetary                                                                                                                      
      + currency_id : Many2one(res.currency)                                                                                                  
    }
                                                                                                                                              
    class "pdp.alloy.type" as AlloyType {                                                                                                     
      + code : Char [required, unique]
      + name : Char [required]                                                                                                                
      + main_metal_id : Many2one(pdp.raw.metal)             
      + purity_system : Selection [carat | millesimal]
    }                                                                                                                                         
   
    class "pdp.alloy.purity" as AlloyPurity {                                                                                                 
      + code : Char [required, unique]                      
      + percent : Float [%]
      + purity_system : Selection [carat | millesimal]                                                                                        
    }
                                                                                                                                              
    class "pdp.alloy" as Alloy {                            
      + type_id : Many2one(pdp.alloy.type)
      + purity_id : Many2one(pdp.alloy.purity)                                                                                                
      + variant : Char [optional]
      -- computed (stored) --                                                                                                                 
      + code : Char  [type.code + purity.code + variant]                                                                                      
      + name : Char  [type.name + purity.code]
      + density : Float  [Σ ratio × metal.density]                                                                                            
      -- computed (volatile) --                             
      + total_ratio : Float  [Σ ratio]                                                                                                        
      -- unique constraint --                               
      ~ (type_id, purity_id, variant)                                                                                                         
      -- service --                                                                                                                           
      + convert_weight(weight, to_alloy) : Float
    }                                                                                                                                         
                                                                                                                                              
    class "pdp.alloy.component" as AlloyComponent {
      + alloy_id : Many2one(pdp.alloy) [cascade]                                                                                              
      + metal_id : Many2one(pdp.raw.metal) [required]       
      + ratio : Float [0.0 – 1.0]                                                                                                             
    }
                                                                                                                                                                                 
                                                            
  AlloyType "0..1" --> "0..1" RawMetal : main_metal_id                                                                                        
  Alloy "0..1" --> "1" AlloyType : type_id
  Alloy "0..1" --> "1" AlloyPurity : purity_id                                                                                                
  Alloy "1" *-- "0..*" AlloyComponent : component_ids       
  AlloyComponent "0..*" --> "1" RawMetal : metal_id                                                                                           
  PdpConfig "0..1" --> "0..1" Alloy : reference_alloy_id    
                                                                                                                                              
  @enduml                                                   
                              
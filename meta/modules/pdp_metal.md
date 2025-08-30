# PDP Metal

A data module that contains the following tables.

class "pdp.metal" 
  - gold : boolean
  - plating : boolean
  - reference : boolean
  - code : char
  - name : char
  - currency_id : m2o→res.currency
  - cost : monetary

class "pdp.metal.purity" 
  - code : char
  - percent : float
  - id : integer

class "pdp.part" 
  - code : char
  - name : char
  - cost_ids : o2m→pdp.part.cost

class "pdp.part.cost" 
  - currency_id : m2o→res.currency
  - part_id : m2o→pdp.part
  - purity_id : m2o→pdp.metal.purity
  - cost : monetary

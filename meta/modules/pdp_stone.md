# PDP Stone

A data module that containts the following tables


class "pdp.stone.category" 
  - active : boolean
  - code : char
  - name : char
  - type_ids : o2m→pdp.stone.type

class "pdp.stone.type" 
  - active : boolean
  - code : char
  - name : char
  - density : float
  - category_id : m2o→pdp.stone.category

class "pdp.stone.shade"
  - code : char
  - shade : char

class "pdp.stone.shape" 
  - code : char
  - shape : char

class "pdp.stone.size"
  - name : char

class "pdp.stone" 
  - code : char
  - cost : monetary
  - currency_id : m2o→res.currency
  - shade_id : m2o→pdp.stone.shade
  - shape_id : m2o→pdp.stone.shape
  - size_id : m2o→pdp.stone.size
  - type_id : m2o→pdp.stone.type

class "pdp.stone.weight" 
  - weight : float
  - shade_id : m2o→pdp.stone.shade
  - shape_id : m2o→pdp.stone.shape
  - size_id : m2o→pdp.stone.size
  - type_id : m2o→pdp.stone.type

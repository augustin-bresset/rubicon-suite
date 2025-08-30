# PDP Price

The module responsible of the price computation.
For each parts of the final price, it compute the cost and margin that result to the cost.

## Wizard

### Price Component

The final price is the result of those component :
* Stone : stone resources
* Metal : metal resources
* Labor : labor on the stone, metal, assembly
* Part : part cost and labor
* Addon : addon labor 

For a given product, margin and date (for gold and currency change), those component will give throught the ***compute*** methode the cost, margin and price value.


#### Price Component : Stone

1. Cost
pdp.product 
  - stone_composition_id : m2o→pdp.product.stone.composition

pdp.product.stone.composition
  - stone_line_ids : o2m→pdp.product.stone

pdp.product.stone
  - pieces : integer
  - stone_id : m2o→pdp.stone

pdp.stone
  - cost : monetary
  - currency_id : m2o→res.currency

2. Margin

pdp.margin.stone
  - margin_id : m2o→pdp.margin
  - stone_type_id : m2o→pdp.stone.type
  

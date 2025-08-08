## Development

### Price Abstract Component

A price component is responsible to compute the **cost** and **margin** that result in the **price**.

Those are the components of the final price:
* Stone : raw material
* Metal : raw material
* Labor : labor on each product (stone, metal and addon)
* Addon : addon on product (painting, lazer)
* Part  : jewelery part made outside (chain, ...)

#### Cost

For each of this component the price comme from :
* stone : pdp.product.stone[Foreign Key : stone_code] -> pdp.stone.cost
* metal : pdp.product.metal (weight) [Foreign Key : metal_code] -> pdp.metal.cost
* labor : max(pdp.labor.cost.product, pdp.labor.model) 
* Addon : pdp.addon.cost


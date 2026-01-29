# ROAD MAP / Remarks

## Actual State

Currently we manage to imports all of the data needed for PDP.

We have two addons :
* Metal Market that give the metal prices per day
* Currency that gives prices per rates (per day)

We have pdp_price that compute the price of a specific product given his margins.

## Metal
We need to add some parameters, those will help us compute the good price given the composition of the metal and how it can be used.

Currently the cost of the metal is compute only from his prices but we do not take into account :
* Risk Factor : for example pink gold have more chances to failed during process
* Material Lost : during polishing, a part of gold can be retrieve, this is not the case for palladium
* Composition : rubicon use his own metal composition for white gold etc



## Pricing
It have to take into account everything.

During pricing, some can change value can change :
* Specific weights
* Specific prices 

Currently stones weight are from pdp.product.stones but the good process is :
* pdp.product.stone weight if not equal to 0 else pdp.stone weight

pdp.product.stone price have to be added


## Environment

* Having the possibility to change mesures like going from gram to ounce


## Backend API
Having a full API that manage the backend with a doc.

This will greatly be usefull for having a clear frontend.

## Frontend
Having a frontend that respect the old version of PDP



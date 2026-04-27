# Sales Information System (SIS)

## Detailed Description 

### Lobby
When you have entered your identifiant, you arrive on the lobby page that have the name of the software `Sales Information System (SIS)`.

![lobby](./images/sis_lobby.png)


### Parties
By clicking on `Parties` a new window appeared named `Maintain Parties`.

![maintainparties](./images/sis_parties_general.png)

The window is here to manage the parties database (or client).

#### Top of the page

By clicking on the down arrow below `Select Party`, a drop-down menu appeared.

![partiesselectparty](./images/sis_parties_selectparty.png)

Here you have all the already record parties in lexicographical order.

Than the general fields are written :
* `Company` name of the company
* `Code` its identifier code, will be written on the series number of products
* `ID` identifier key in the database
* `Inactive` (bool) by default is False

Those fields are the required fields needed for having an instance of Party and so for his creation.

On this case we arrived on :
* `Company` : A&J INTERNATIONAL
* `Code` : A&J
* `ID` : 7
* `Inactive` : False

And a drop-down menu `Select Party` with all the parties already in the database. Here we have on `A&J INTERNATIONAL`. 

The following fields are nullable.

#### General

By clicking on `General` (default view) you have a view of the general information (Contact, Address, etc)

![partiesgeneral](./images/sis_parties_general.png)

Here you can edit those fields :
* `Contact` the name of the contact person in the company
* `Title` the title of the contact person in the company
* `Address` the address of the company with those fields : Country, City, State, Zip
* `Group` Not sure yet
* `Phones` the phone number of the company
* `Email` the email of the company
* `Fax` the fax number of the company
* `Home Page` the website of the company
* `Notes` any notes on the company and followed by the same text, a kind of contract redundant message.

On this situation we have for `A&J INTERNATIONAL` :

* `Contact` : Mr. Jose V. ROSAS
* `Title` : (empty)
* `Address` : 
    * KLEX CORPORATION
    * 7905 S.W. 86 STREET SUITE 601
    * `city` : MIAMI
    * `state` : FL
    * `zip` : 33143
    * `country` : UNITED STATES OF AMERICA
* `Group` : (empty)
* `Phones` : 
    * 52 333 121 3410
    * 52 333 641 1423
* `Fax` : 52 333 122 1891
* `Email` : mailto:coloradojr@gmail.com
* `Home Page` : (empty)
* `Notes` : mobile 089-0440321 


#### Defaults
By clicking on `Defaults` the following view is displayed.

![partiesdefaults](./images/sis_parties_defaults.png)

If you tick `Is a Vendor`, it display more options.

You can edit those fields here :
Account, Margin, PayTerm.

![partiesdefaultsvendor](./images/sis_parties_defaults_vendor.png)

The drop-down menu `Margin` contains the one that are managed on `PDP`.

Remarks :
 * Account is generally empty

    If find only two parties that contains it 
    * Kemeya : BKK Feb 12
    * Tank : 18%

 * The `Vendor` is generally no used. Only two occurences found :
    * Lenovre Jewelery
    * TC

So those fields are considered useless.

In the case of `A&J INTERNATIONAL` we have :
* `Is a Customer` : True
* `Is a Vendor` : False
* `Account` : (empty)
* `Margin` : Wholesale
* `PayTerm` : T/T


#### Shipment Info
By clicking on `Shipment Info`  the following view is displayed.

![partiesshipmentinfo](./images/sis_parties_shipmentinfo.png)

You can edit those fields here :
* `Address` the address where the products are shipped to, in the same format as the one in `General`
* `Default Method` the default shipping method
* `Fed. Ex. Acc.` the federal express account
* `Stamp.` the stamp information

In the case of `A&J INTERNATIONAL` we have :
* `Address` :
    * KLEX CORPORATION
    * 7905 S.W. 86 STREET SUITE 601
    * `City` : MIAMI
    * `State` : FL
    * `Zip` : 33143
    * `Country` : UNITED STATES OF AMERICA
* `Default Method` : Courier
* `Fed. Ex. Acc.` : TEL: 1 305 412 7477 / FAX: 1 305 412 8404
* `Stamp.` : 750 + 2


#### Bank Info
By clicking on `Bank Info`  the following view is displayed.

![partiesbankinfo](./images/sis_parties_bankinfo.png)

You can edit those fields here :
* `Bank Name` the name of the bank of the company
* `Address` the address of the bank in three lines : address, ZIP + City, COUNTRY
* `Acc. Name` the name of the account
* `Acc. No.` the number of the account

In the case of `A&J INTERNATIONAL` we have :
* `Bank Name` : NEUFLIZE OBC Enterprises
* `Address` :
    * 3, ave Hoche
    * 75008 PARIS
    * FRANCE
* `Acc. Name` : Emasur BIC: NSMEFRPPXXX
* `Acc. No.` : IBAN: FR35 1497 8801 0019240 NCV 00 C93


#### New 

By clicking on `+`, display an empty Party.

![partiesnewblank](./images/sis_parties_new_general.png)
From here in `Defaults`, `Shipment Info` and `Bank Info` are blank in the same way as `General`.

The `ID` field have been automatically created. It seems to increment of one for each party created.

For adding a new party you have to fill the general field at the top first `Company` and `Code`. `Inactive` is by default on *False*.

Then you can click on `Save` to create the instance.

If you do not do it SIS will send an error.
![partiesnewerror](./images/sis_parties_errorupdatefailed.png)

This error will also be send if you empty one of the general field on an instance.

###  Quotations, Book Orders and Shipment Goods

Those pages are quite similar. We will called the general format a `Document` Manager window.

By clicking on `Quotations` you arrived on `Maintain Sales Quotations.`, this is used with new client or client where there is a possibility of `Cancellation`. 
![quotations](./images/sis_quotations_general.png)

By clicking on `Book Orders` you arrived on `Maintain Sales Orders.`, this is used to  manage and create **Sales Orders**.
![orders](./images/sis_orders_general.png)

By clicking on `Shipment Goods` you arrived on `Maintain Sales Invoices.`, this is used to manage and create **Invoices**.
![invoices](./images/sis_invoices_default.png)


Here you can see that they are almost exactly the same. In `Orders` you can find one more option, the menu `Order`. So we will focus on the `Sales Orders` pages.


#### Required Field

On the top of the page you can find the required fields.

* `Doc Name` name of the document
* `ID` identifier in the database
* `Closed` boolean 
* `Margin` choices on of the margins manage in PDP
* `Created` date of creation
* `Due Date` date of the expecting result (delivry limit for exemple)

In our case we have for the sales order 

* `Select Document` : 2025
    Drop down menu : EMA-25001
* `Doc Name` : SO-EMA-25001
* `ID` : 13159
* `Closed` : True
* `Margin` : Emasur
* `Created` : 06/02/2025
* `Due Date` : 31/01/2025


#### General

By clicking on `General` (open by default), the following view is displayed.

![ordersgeneral](./images/sis_orders_general.png)

You can edit those fields here :
Customer, Address, Ship By, Payement, Stamp, Notes, Foot notes.

In our case :
* `Customer` : EMASUR
* `Address` :
    * EMASUR
    * 12, RUE DE LA PAIX
    * PARIS, 75002
    * FRANCE Tel:+331 4770 0223
    * 
* `Ship By` : Courier
* `Payement` : T/T
* `Stamp` : EMA+IL

* `Notes` : Gold:2645$
* `Foot notes` : The seller hereby ... (common message)




#### Items/General
When you click on `Items` you have a five sub-menu : `General`, `Instructions`, `Sizes`, `Weights` and `Profit`. 
And a check box : `Item Closed`
In our case `Item Closed` is ticked.

By clicking on `Items/General`, the following view is displayed.
By default the `General` sub-menu has opened.

![ordersitemsgeneral](./images/sis_orders_items_general.png)

It contains a table with those fields :
* Design (`MODEL-COLORS/M`)
* Purity 
* Qty
* Currency
* U.Price
* Amount
* Description

You can find the references of the products ordered by the customer. With multiple informations.

In our case (only one design): 
* `Design` : P720-RHO+LAM+GT+PT/P
* `Purity` : 18K
* `Qty` : 1
* `Currency` : US$
* `U.Price` : 195
* `Amount` : 195
* `Description` : (IL) 12 MM. WITH LTSA LIGHT STONE COLOUR


#### Items/Instructions

By clicking on `Items/Instructions`, the following view is displayed.
By default the `Instructions` sub-menu has opened.

![ordersitemsinstructions](./images/sis_orders_items_instructions.png)

It contains a table with those fields :
* Design (`MODEL-COLORS/M`)
* Item Group 
* Special Instruction


You can find the references of the products ordered by the customer with the fields `ItemGoup` and `Special Instruction`.

In our case : 
* `Design` : P720-RHO+LAM+GT+PT/P
* `Item Group` : #8001 ADC  EMAIL 27/12/2024
* `Special Instruction` : (IL) 12 MM. WITH LTSA LIGHT STONE COLOUR

#### Items/Sizes

By clicking on `Items/Sizes`, the following view is displayed.
By default the `Sizes` sub-menu has opened.

![ordersitemssizes](./images/sis_orders_items_sizes.png)

It contains a table with those fields :
* Design (`MODEL-COLORS/M`)
* Qty
* Size Remarks

You can find the references of the products ordered by the customer with the fields `Qty` and `Size Remarks`.

In our case :
* `Design` : P720-RHO+LAM+GT+PT/P
* `Qty` : 1
* `Size Remarks` : (empty)



#### Items/Weights

By clicking on `Items/Weights`, the following view is displayed.
By default the `Weights` sub-menu has opened.

![ordersitemsweights](./images/sis_orders_items_weights.png)

It contains a table with those fields :
* Design (`MODEL-COLORS/M`)
* Purity
* Qty
* Diamonds
* Stones
* Diverse
* Metal
* Weight

You can find the references of the products ordered by the customer with fields that details the weight.

In our case :
* `Design` : P720-RHO+LAM+GT+PT/P
* `Purity` : 18K
* `Qty` : 1
* `Diamonds` : 0
* `Stones` : 0
* `Diverse` : 0
* `Metal` : 1.1
* `Weight` : 1.1

#### Items/Profit

By clicking on `Items/Profit`, the following view is displayed.
By default the `Profit` sub-menu has opened.

![ordersitemsprofit](./images/sis_orders_items_profit.png)

It contains a table with those fields :
* Design (`MODEL-COLORS/M`)
* Purity
* Qty
* U. Cost
* Cost
* Amount
* Profit
* Profit %

This table details the profit calculation by reference.

In our case :
* `Design` : P720-RHO+LAM+GT+PT/P
* `Purity` : 18K
* `Qty` : 1
* `U. Cost` : 118.03
* `Cost` : 118.03
* `Amount` : 195
* `Profit` : 76.97
* `Profit %` : 65.21


#### Order

By clicking on `Order`, the following view is displayed.

![ordersorder](./images/sis_orders_order.png)

You can edit those fields here :

* `Cust P.O. No.` stands for *Customer Purchase Order Number*, this is the reference number from the client.

* `Rcv, Mode` stands for *Receiving Mode*.

* `Trade Fair` is used if the order was made during one.

* `Employee` contains the name of the employee responsible of this order.

In our case we have :
* `Cust P.O. No.` : #8001
* `Rcv, Mode` : Email
* `Trade Fair` : (empty)
* `Employee` : ORM

And on the right a table that contains the column :
* `Ring Size`
* `Alloc %`

In our case, is empty.

#### Shipment

By clicking on `Shipment`, the following view is displayed.

![ordersshipment](./images/sis_orders_shipment.png)

You can edit those fields here :
Ship to this Address (bool), Consignee Bank (bool), For Acc. Of, Book, Page

If needed, you can specify delivery details here.

In our case the boxe are not ticked and the fields are empty.


#### Child Documents

By clicking on `Child Documents`, the following view is displayed.

![orderschilddocuments](./images/sis_orders_childdocuments.png)

It contains a table with only one field `DocName` (`DOCTYPE-AAA-XXXXX`). 

List `Document` that come from the current one. In this case we have a sale order SO-EMA-250001 which has been sent through the sale invoice SI-EMA-250003.

It can happen that multiple invoices are used for one order. And than on one invoice it contains product from differents sales order.

In our case we have only one child document : SI-EMA-250003.

#### Profit Details

At the bottom of the page you have the details of the profit. 

![ordersdetailsprofit](./images/sis_orders_general.png)

It contains those fields that are computed automatically.
* Total F.O.B Bangkok US$
* Add Freight and Insurance US$
* Total C.I.F PARIS US$
And 
* Less Deposit
* Total

Finally on the right you can specify the currency with a drop-down menue.
And an other table show :
* Qty
* Amount
* Less Cost
* Profit
* Profit in %

In our case we have :
* `Total F.O.B Bangkok US$` : 195.00
* `Add Freight and Insurance US$` : 0.00
* `Total C.I.F PARIS US$` : 195.00
* `Less Deposit` : 0.00
* `Total` : 195.00

And on the right :

* `Qty` : 1
* `Amount` : 195.00
* `Less Cost` : 118.03
* `Profit` : 76.97
* `Profit in %` : 65.21


#### New

By clicking on `New` at the bottom of the page, a new instance of a sales is created.
![ordersprint](./images/sis_orders_new.png)

All the fields `Items`, `Order`, `Shipment` and `Child Document` are empty like `General`.

We can notice that **by default** the document type is indicate:
* `Doc Name` : 
    * `SQ-` for `Quotations`
    * `SO-` for `Sales Order`
    * `SI-` for `Sales Invoice`
* `ID` : automatically created by incremeting from the last one
* `Closed` : False by default
* `Margin` :  Wholesale
* `Created` : the current date 
* `Due Date` : One monthe after the current date


#### Print

By clicking on `Print` at the bottom of the page, the window `Print Document` will be displayed.

![ordersprint](./images/sis_orders_print.png)


With on the right `Markup %` set to 0.00. 

Here we can notice :
* `With Weights` : Print the sales orders/quotations with the weights details

Remarks : 
* Actually only the `With Weights` format is used.


#### Prices
By clicking on `Prices` at the bottom of the page, the window `Product Prices.` will be displayed.

![ordersprices](./images/sis_orders_prices.png)

Here you can indicate :
* Model
* Conv (other metal than white gold)
* Purity
* Qty 
* Select a design
It will gives you on two tables details on the product.
One table with Metal, Weight and the other with Stone, Pcs, Weight
Then you have at the top the field `Price` that indicate the price, you can also choose the currency with a drop-down menu.

In our case we have :
* `Model` : R102
* `Conv` : None
* `Purity` : 18K
* `Qty` : 1

And it give the price : 1716 US$.
Then on the tables we have :

* `Design` (one design) : R102-GA+OR+YS+YM+TT/W

Then on the right/High (one line) :
* `Metal` : White Gold
* `Weight` : 11.8

Then on the right/Low (three lines) :
* `Stone` : Diamond, Garnet, Saphire
* `Pcs` : 21, 25, 56 
* `Weight` : 0.1385, 5.9165, 0.55 


A table at the bottom seems to refers to similar orders. It contains those fields :
* Last Purc. On
* DocName
* Qty
* Uprice
* Amount

In our case all empty.

And a drop-down menu allows you to select a specific customer.

On this window you can search in the database manage by PDP the model and references of products. It allows you too indicate the appropriate prices for each item.

At the bottom you also have Margin, Change by % and tick box `Round off`.
In our case we have :
* `Margin` : NET+30%
* `Change by %` : 0.00
* `Round off` : False (not ticked)

#### Copy
By clicking on `Copy` at the bottom of the page, the window `Document Browser` will be displayed.

![orderscopy](./images/sis_orders_copy.png)

Here you can filter by `Doc. Types` and `Doc.` with a drop-down menu and by their boolean attribute : `Open`, `Closed`, `Canceled` with tick boxes.

Then on the table bellow it, the documents appeared with those fields :
* Document (`DOCTYPE-AAA-XXXXX`)
* Cust. PO. (empty here)
* Company
* Created (date)
* Due (date)
* Qty
* Amount

Then a second table where you can filter with the field `Serial` contains those fields :
* Ref. Document
* Design
* Purity
* Qty
* Qty Ship.
* QtyBal
* Uprice
* Amount
* ItemGroup
* SizeRemarks
* ...

This window allows you to copy `Item` from other `Document` of any kind.
Because you are on `Sales Orders` it look at `Sales Quotation` by default. 


#### Customers
By clicking on `Customers` at the bottom of the page, the window `Maintain Parties` will be displayed.

![orderscustomers](./images/sis_parties_general.png)

#### Metal Weight Summary
By clicking on `Metal Req.` at the bottom of the page, the window `Metal Weight Summary` will be displayed.

![orderscustomers](./images/sis_orders_metal_req.png)

It contains a table with two fields : 
* GoldType (`M-PURITY`)
* Grams

In this case :
* `GoldType` : P-18K, Y-18K
* `Grams` : 28.92, 33.45

#### Toolbar Maintain

By Clicking on `Maintain` you have a drop-down menu that appeared.

![toolbarmaintain](./images/sis_orders_maintain.png)
With only `Parties` that will open the `Maintain Parties` window seen before.

#### Toolbar Tools

By Clicking on `Tools` you have a drop-down menu that appeared.

![toolbartools](./images/sis_orders_tools.png)

It contains those options :
* Doc. Browser : open the `Document Browser` window
* Product Browser : open the `Product Prices` window such as seen later 
* Update Weight
* Update Weights (All Items)
* Update Costs from PDP
* Update Cost and Prices from PDP
* Calculate Prices from Raw Material

All the ones that start with `Update` will check if changes occured on the database and will refresh accordingly the data.

Finally by clicking on `Calculate Prices from Raw Material`, the window `Update Price from Raw-Material` is displayed. 


![orderstoolscalculatepricesfromraw](./images/sis_orders_tools_updatepricefromraw.png)

Here you can fill two fields :
* Diamond Rate
* Metal Rate
Then there is two buttons `Start` and `Cancel`.



### Lobby Application

On the toolbar, if you click on `Application` a drop-down menue appeared.
![lobbyapplication](./images/sis_lobby_application.png)
Here you have an `Exit` button.

### Lobby Maintain

On the toolbar, if you click on `Maintains` a drop-down menue appeared.
![lobbymaintain](./images/sis_lobby_maintain.png)

It contains those options :
* Parties
* Sales
* Production
* Misc. Info.

#### Parties

`Parties` will open the `Maintain Parties` window.

#### Sales
Clicking on `Sales` will display other possibilities on the drop-down menu.
![lobbymaintainsales](./images/sis_lobby_maintain_sales.png)

* Quotations
* Orders
* Consignment
* Consignment Return
* Invoices
* Sales Returns
* Repairs

All those sales documents have been seen earlier or have more or less the same format has `Quotations`, etc. It is other `Document Type` but less common.

#### Production 

Clicking on `Production` will display other possibilities.

![lobbymaintainproduction](./images/sis_lobby_maintain_production.png)

Which is also a `Document` manager window but his goal is unclear.

#### Misc Info

Clicking on `Misc. Info.` will open the window `Miscellaneous Information`. 
This window manage multiple table of general information. You can edit those information and save them by clicking on `Save` at the bottom-right of the page.

##### Business Areas
![lobbymaintainmiscbusinessareas](./images/sis_lobby_maintain_miscinfo_businessareas.png)

Such as : 
* `Region` : ID , Region
* `Country`: ID, Country, Region
on the `Business Areas` sub-window.

##### Trade Fairs
Such as `Fair` on the `Trade Fairs` sub-window.
![lobbymaintainmisctradefairs](./images/sis_lobby_maintain_miscinfo_tradefairs.png)

That contain for each `Fair` :
* FairID
* Fair
* City
* Country
* Start (date)
* End (date)

##### Pay and Ship Methods
Such as `Payment` and `Shipment` methods on the `Pay and Ship Methods` sub-window.
![lobbymaintainmiscpayandshipmethods](./images/sis_lobby_maintain_miscinfo_payandshipmethods.png)

That contains two tables :
* Patment Terms (certainly payment terms) : ID, Payment Term
* Shipment Methods : ID, Shipment Method

##### Company Info

Such as `Account` info on the `Company Info` sub-window.

![lobbymaintainmisccompanyinfo](./images/sis_lobby_maintain_miscinfo_companyinfo.png)

With a two fields named `Account Info.`.

### Lobby Reports

On the toolbar, if you click on `Reports` a drop-down menue appeared.
![lobbyreports](./images/sis_lobby_reports.png)

It contains those options :
* Production Order Forms
* Spec. Sheet
* Document Pictures
* Customer List
* Customer Price List
* Yearly Customer Sales
* Customer Price List with Detail to Excel
* Shipment Labels
* Shipment Balance
* Shipment Ledger
* Best Sellers
* BEst Sellers Model

#### Production Order Forms

By clicking on `Production Order Forms` other possibilities are displayed.
![lobbyreports](./images/sis_lobby_reports_productionorderforms.png)

* Assorting
* Stone Summary
* Casting
* Filling
* Stock Card

##### Shipment Labels

By clicking on `Shipment Labels` other possibilities are displayed.
![lobbyreports](./images/sis_lobby_reports_shipmentlabels.png)

* Big Labels
* Small Labels

##### Report

All of the options that are in this menu allows you to create an appropriate reports. 

Clicking on one of these options will either generate the report directly or display the `Parameters window.

![lobbyreportsparameters](./images/sis_lobby_reports_parameters.png)



In this window, you can filter by :
* `Document` (year, type, ref,)
* `Customer` (name)
* `Stone`
* `Ornament Catagory`
* `Date Range` (between when and when)
* `Design`

And click on `Ok` to generate the report.

### Lobby Tools

On the toolbar, if you click on `Tools` a drop-down menue appeared.
![lobbytools](./images/sis_lobby_tools.png)

By clicking on `Document Browser` a window with the same name will open.
![lobbytoolsdocumentbrowser](./images/sis_lobby_tools_documentbrowser.png)
It allow you to search through all the kinds of `Documents` regardless their type (`Sales Order`, ...)

By clicking on `Product Browser` the window `Product Prices` will open.
![lobbytoolsproductbrowser](./images/sis_lobby_tools_productprices.png)

It allow you to search through the `Product` by entering the `Model` name and selecting the `Design`.

By clicking on `Analysis` one more drop-down menue appeared.
![lobbytoolsanalysis](./images/sis_lobby_tools_analysis.png)

But by clicking on any of those two options `Order Analysis` and `Sales Analysis`, nothing happen.

### Lobby Help

On the toolbar, if you click on `Help` a drop-down menue appeared.
![lobbyhelp](./images/sis_lobby_help.png)

The button `About` will open.
This is useless.





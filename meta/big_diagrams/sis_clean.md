@startuml
skinparam classAttributeIconSize 0

' === Classes (Tables) ===

class Countries {
  +CountryID : char(2)
  Country : varchar(50)
  RegionID : char(2)
}

class Regions {
  +RegionID : char(2)
  Region : varchar(50)
}

class Customers {
  +CustID : int
  CustCode : varchar(10)
  Company : varchar(50)
  CustGroup : varchar(15)
  Add1 : varchar(50)
  Add2 : varchar(50)
  Add3 : varchar(50)
  Add4 : varchar(50)
  City : varchar(20)
  State : char(10)
  Zip : varchar(12)
  CountryID : char(2)
  Phone1 : varchar(20)
  Phone2 : varchar(20)
  Fax : varchar(20)
  Email : varchar(50)
  HomePage : varchar(50)
  CustAcctID : varchar(10)
  MarginID : char(5)
  SalesPayTermID : tinyint
  SalesShipperID : tinyint
  VendAcctID : varchar(10)
  PurchasePayTermID : tinyint
  Notes : text
  Inactive : bit
  Contact : varchar(25)
  Title : varchar(25)
  Customer : bit
  Vendor : bit
  ShipAdd1 : varchar(50)
  ShipAdd2 : varchar(50)
  ShipAdd3 : varchar(50)
  ShipAdd4 : varchar(50)
  ShipCity : varchar(20)
  ShipState : char(10)
  ShipZip : varchar(12)
  ShipCountryID : char(2)
  BankName : varchar(50)
  BankAdd1 : varchar(50)
  BankAdd2 : varchar(50)
  BankAdd3 : varchar(50)
  BankAccName : varchar(50)
  BankAccNo : varchar(50)
  FedExAccount : varchar(255)
  Stamp : varchar(50)
}

class PayTerms {
  +PayTermID : tinyint
  PayTerm : varchar(15)
}

class Shippers {
  +ShipperID : tinyint
  Shipper : varchar(15)
}

class DocInMode {
  +InModeID : tinyint
  InMode : char(10)
}

class TradeFairs {
  +FairID : int
  Fair : varchar(50)
  FairCountryID : char(2)
  FairCity : varchar(20)
  StartDate : datetime
  EndDate : datetime
}

class DocTypes {
  +DocTypeID : char(3)
  DocType : varchar(50)
  DocCatagory : char(1)
}

class SalesDocs {
  +DocTypeID : char(3)
  +DocID : int
  DocIDStr : varchar(5)
  DocName : varchar(15)
  CreateDate : datetime
  DelvDate : datetime
  CustID : int
  Stamp : varchar(50)
  CustPO : varchar(15)
  ShipperID : tinyint
  PayTermID : tinyint
  EmpID : varchar(10)
  Notes : text
  InModeID : tinyint
  FairID : int
  TotalQty : decimal(10, ?)
  TotalCost : decimal(18, ?)
  TotalProfit : decimal(18, ?)
  FOBTitle : varchar(30)
  CurrID : char(2)
  TotalAmount : decimal(18, ?)
  Deposit : decimal(18, ?)
  SubTotal : decimal(18, ?)
  FreightTitle : varchar(30)
  Freight : decimal(18, ?)
  CIFTitle : varchar(30)
  CIF : decimal(18, ?)
  Book : int
  Page : int
  Closed : bit
  Canceled : bit
  ConsigneeBank : bit
  ShipToAdd : bit
  Add0 : varchar(50)
  Add1 : varchar(50)
  Add2 : varchar(50)
  Add3 : varchar(50)
  Add4 : varchar(50)
  BankName : varchar(50)
  BankAdd1 : varchar(50)
  BankAdd2 : varchar(50)
  BankAdd3 : varchar(50)
  BankAccName : varchar(50)
  BankAccNo : varchar(50)
  ShipAdd1 : varchar(50)
  ShipAdd2 : varchar(50)
  ShipAdd3 : varchar(50)
  ShipAdd4 : varchar(50)
  TotalWeight : decimal(18, ?)
  FootNotes : text
}

class SalesDocItems {
  +DocTypeID : char(3)
  +DocID : int
  SubDocTypeID : char(3)
  SubDocID : int
  Design : varchar(25)
  SubDocName : varchar(15)
  SNo : int
  CatID : char(2)
  OrnID : char(7)
  StoneID : varchar(20)
  GoldID : varchar(7)
  Purity : char(5)
  Descr : varchar(150)
  Qty : decimal(10, ?)
  QtyINOUT : decimal(10, ?)
  QtyBal : decimal(11, ?)
  UPrice : decimal(18, ?)
  Amount : decimal(18, ?)
  Instrs : varchar(150)
  StockID : varchar(10)
  Closed : bit
  Canceled : bit
  UCost : decimal(18, ?)
  Cost : decimal(18, ?)
  Profit : decimal(18, ?)
  WgtDiamonds : decimal(18, ?)
  WgtStones : decimal(18, ?)
  WgtDiverse : decimal(18, ?)
  WgtMetal : decimal(18, ?)
  Weight : decimal(18, ?)
  SizeRemarks : varchar(30)
  DiamQuality : char(5)
  CurrID : char(2)
  ItemGroup : varchar(50)
  UnkID : int
}

class DocOrnSizePers {
  +DocTypeID : char(3)
  +DocID : int
  OrnSize : varchar(15)
  AllocPer : int
}

class DocItemStoneDetail {
  +DocTypeID : char(3)
  +DocID : int
  SubDocTypeID : char(3)
  SubDocID : int
  SubDocName : varchar(15)
  SNo : int
  Design : varchar(25)
  CatID : char(2)
  OrnID : char(7)
  StoneID : varchar(20)
  GoldID : varchar(7)
  Purity : char(5)
  StoneGroup : char(2)
  StoneCatID : char(1)
  StoneCatName : varchar(50)
  TypeID : char(5)
  TypeName : varchar(20)
  ShapeID : char(5)
  ShapeName : varchar(20)
  StoneSize : varchar(10)
  ShadeID : char(5)
  ShadeName : varchar(25)
  Qty : decimal(10, ?)
  Pcs : smallint
  ExtPcs : decimal(16, ?)
  PurWgt : decimal(24, ?)
  ExtPurWgt : decimal(35, ?)
  ShapeID2 : char(5)
  ShapeName2 : varchar(20)
  StoneSize2 : varchar(10)
  InvWgt : decimal(24, ?)
  ExtInvWgt : decimal(35, ?)
}

class OrderQtySum {
  +DocTypeID : char(3)
  +DocID : int
  DocName : varchar(15)
  ItemGroup : varchar(50)
  Design : varchar(25)
  Purity : char(5)
  OrderQty : decimal(38, ?)
  UPrice : decimal(18, ?)
  OrderAmt : decimal(18, ?)
}

class ShipBal {
  Alpha : varchar(1)
  Company : varchar(50)
  DocTypeID : char(3)
  DocID : int
  DocName : varchar(15)
  CreateDate : datetime
  DelvDate : datetime
  DueMonth : int
  DueYear : int
  Design : varchar(25)
  Purity : char(5)
  ItemGroup : varchar(50)
  OrderQty : decimal(10, ?)
  ShipQty : decimal(10, ?)
  QtyBal : decimal(11, ?)
  UPrice : decimal(18, ?)
  OrderAmt : decimal(18, ?)
  ShipAmt : decimal(29, ?)
  AmtBal : decimal(30, ?)
  Descr : varchar(150)
  Instrs : varchar(150)
}

class ShipLedger {
  DocTypeID : char(3)
  DocName : varchar(15)
  CustID : int
  OrderDate : datetime
  Grp : varchar(101)
  ItemGroup : varchar(50)
  Design : varchar(25)
  Purity : char(5)
  Qty : decimal(10, ?)
  Amount : decimal(18, ?)
}

class ShipQtySum {
  DocTypeID : char(3)
  DocID : int
  DocName : varchar(15)
  SubDocTypeID : char(3)
  SubDocID : int
  ItemGroup : varchar(50)
  Design : varchar(25)
  Purity : char(5)
  ShipQty : decimal(38, ?)
  Weight : decimal(18, ?)
}

class SubDocCheck {
  DocTypeID : char(3)
  DocID : int
  Design : varchar(25)
  Purity : char(5)
}


' === Relationships (Foreign Keys) ===

Countries      --> Regions         : RegionID
Customers      --> Countries       : CountryID
Customers      --> PayTerms        : SalesPayTermID
Customers      --> Shippers        : SalesShipperID
Customers      --> Countries       : ShipCountryID
TradeFairs     --> Countries       : FairCountryID
SalesDocs      --> DocTypes        : DocTypeID
SalesDocs      --> Customers       : CustID
SalesDocs      --> Shippers        : ShipperID
SalesDocs      --> PayTerms        : PayTermID
SalesDocs      --> DocInMode       : InModeID
SalesDocs      --> TradeFairs      : FairID
SalesDocItems  --> SalesDocs       : DocTypeID,DocID
DocOrnSizePers --> SalesDocs       : DocTypeID,DocID
DocItemStoneDetail --> SalesDocs   : DocTypeID,DocID
OrderQtySum    --> SalesDocs       : DocTypeID,DocID
ShipBal        --> SalesDocs       : DocTypeID,DocID
ShipLedger     --> Customers       : CustID
ShipQtySum     --> SalesDocs       : DocTypeID,DocID
SubDocCheck    --> SalesDocs       : DocTypeID,DocID

@enduml

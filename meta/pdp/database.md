@startuml
' =========================
' Schema: dbo
' =========================

'-- Classes (Tables) Definitions --

class ComponentTree {
    + AbsID : int [PK]
    + ParentID : varchar(20)
    + NodeID : varchar(20)
    + NodeName : varchar(20)
    + TextID : varchar(40)
    + Margin : decimal(18)
    + NodeLevel : int
    + Sort : int
}

class Conditions {
    + Condition : char(2) [PK]
    + CondDesc : varchar(50)
}

class Countries {
    + CountryID : char(2) [PK]
    + CountryName : varchar(50)
    + LangName : varchar(50)
    + CurrName : varchar(15)
    + BaseCountry : tinyint
    + Rate : decimal(18)
}

class dtproperties {
    + id : int [PK, Identity]
    + objectid : int
    + property : varchar(64)
    + value : varchar(255)
    + uvalue : nvarchar(255)
    + lvalue : image
    + version : int
}

class Excel {
    + Design : varchar(25) [PK]
    + CatName : varchar(25)
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + TypeID : char(5)
    + ShadeID : char(5)
    + ShapeID : char(5)
    + StoneSize : varchar(10)
    + Pcs : smallint
    + UnitWgt : decimal(18)
    + TotalWgt : decimal(24)
    + InCollection : bit
}

class GetPrices {
    + MarginID : varchar(5) [PK]
    + Design : varchar(25)
    + Design2 : varchar(25)
    + Purity : char(5)
    + Currency : char(2)
    + MetalConvto : char(2)
    + MetalCost : decimal(38)
    + MetalPrice : decimal(38)
    + MetalMargin : decimal(38)
    + StoneCost : decimal(38)
    + StonePrice : decimal(38)
    + StoneMargin : decimal(38)
    + PartsCost : decimal(38)
    + PartsPrice : decimal(38)
    + PartsMargin : decimal(38)
    + MiscCost : decimal(38)
    + MiscPrice : decimal(38)
    + MiscMargin : decimal(38)
    + LaborCost : decimal(38)
    + LaborPrice : decimal(38)
    + LabotMargin : decimal(38)
    + Cost : decimal(38)
    + Price : decimal(38)
    + Margin : decimal(38)
}

class Globals {
    + Name : varchar(50) [PK]
    + Description : text
    + vInt : int
    + vDec : decimal(18)
    + vImg : image
    + vText : text
    + vChar : char(255)
}

class Grades {
    + Grade : char(2) [PK]
}

class LaborTypes {
    + LaborTypeID : char(3) [PK]
    + LaborType : varchar(10)
    + DefUCost : decimal(18)
    + DefUCostCurrID : char(2)
}

class Margins {
    + MarginID : varchar(5) [PK]
    + MarginName : varchar(50)
    + OverAllMargin : decimal(18)
    + Inactive : bit
    + PartsMargin : decimal(18)
    + LaborMargin : decimal(18)
    + CastingMargin : decimal(18)
    + StoneMargin : decimal(18)
}

class MatchingModels {
    + CatID : char(2) [PK, FK → Models.CatID]
    + OrnID : char(5) [PK, FK → Models.OrnID]
    + CatID2 : char(2)
    + OrnID2 : char(5)
}

class MetalConv {
    + MetalID : char(2) [PK, FK → Metals.MetalID]
    + MetalID2 : char(2)
    + ConvPer : decimal(18)
}

class MetalMargins {
    + MarginID : varchar(5) [PK, FK → Margins.MarginID]
    + ProdCatID : char(5)
    + Purity : char(5) [FK → MetalPurities.Purity]
    + MetalMargin : char(10)
}

class MetalPurities {
    + Purity : char(5) [PK]
    + PurityPer : decimal(10)
}

class MetalPurityConv {
    + Purity : char(5) [PK, FK → MetalPurities.Purity]
    + Purity2 : char(5)
    + ConvPer : decimal(18)
}

class Metals {
    + MetalID : char(2) [PK]
    + MetalName : varchar(50)
    + MetalUCost : decimal(18)
    + MetalUCostCurrID : char(2)
    + ApplyPlating : bit
}

class MiscMargins {
    + MiscTypeID : char(3) [PK, FK → MiscTypes.MiscTypeID]
    + MarginID : varchar(5) [PK, FK → Margins.MarginID]
    + MiscMargin : decimal(18)
}

class MiscTypes {
    + MiscTypeID : char(3) [PK]
    + MiscType : varchar(10)
    + DefUCost : decimal(18)
    + DefUCostCurrID : char(2)
}

class ModelLabor {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + GoldID : varchar(4)
    + Labor : decimal(18)
    + Casting : decimal(18)
    + Filing : decimal(18)
    + Polishing : decimal(18)
    + LaborCurrID : char(2)
    + TotLabor : decimal(21)
}

class ModelMetal {
    + CatID : char(2) [PK, FK → Models.CatID]
    + OrnID : char(5) [PK, FK → Models.OrnID]
    + GoldID : varchar(4)
    + MetalID : char(2) [FK → Metals.MetalID]
    + Purity : char(5) [FK → MetalPurities.Purity]
    + Weight : decimal(18)
}

class ModelMetalParts {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + GoldID : varchar(4)
    + MetalID : char(2)
    + Part : varchar(10)
    + Qty : int
}

class Models {
    + CatID : char(2) [PK, FK → OrnCatagories.CatID]
    + OrnID : char(5) [PK]
    + OrnIDNum : int
    + DrawingNum : varchar(30)
    + QuotationNum : varchar(30)
}

class ModelStone {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + StoneID : varchar(14)
    + TypeID : char(5) [FK → StoneTypes.TypeID]
    + SetID : smallint [FK → StoneSettings.SetID]
    + ShapeID : char(5) [FK → StoneShapes.ShapeID]
    + StoneSize : varchar(10) [FK → StoneSizes.StoneSize]
    + ShadeID : char(5) [FK → StoneShades.ShadeID]
    + Pcs : smallint
    + Weight : decimal(18)
    + StoneUnitCost : decimal(18)
    + StoneCost : decimal(18)
    + StoneCostCurrID : char(2)
    + SetUnitCost : decimal(18)
    + SetCost : decimal(18)
    + SetCostCurrID : char(2)
    + ShapeID2 : char(5)
    + StoneSize2 : varchar(30)
    + Weight2 : decimal(18)
    + LineNum : varchar(5)
}

class OrnCatagories {
    + CatID : char(2) [PK]
    + CatName : varchar(25)
    + CatName2 : varchar(25)
    + MetalWast : decimal(18)
}

class Parts {
    + PartID : varchar(5) [PK]
    + PartName : varchar(20)
}

class PartsCost {
    + PartID : varchar(5) [PK, FK → Parts.PartID]
    + Purity : char(5) [FK → MetalPurities.Purity]
    + PartUCost : decimal(18)
    + PartUCostCurrID : char(2)
}

class Prices {
    + MarginID : char(5)
    + Design : varchar(25)
    + Design2 : varchar(25)
    + Purity : char(3)
    + Currency : char(2)
    + MetalConvto : char(1)
    + MetalCost : decimal(18)
    + MetalPrice : decimal(18)
    + MetalMargin : decimal(18)
    + StoneCost : decimal(18)
    + StonePrice : decimal(18)
    + StoneMargin : decimal(18)
    + PartsCost : decimal(18)
    + PartsPrice : decimal(18)
    + PartsMargin : decimal(18)
    + MiscCost : decimal(18)
    + MiscPrice : decimal(18)
    + MiscMargin : decimal(18)
    + MiscCost2 : decimal(18)
    + MiscPrice2 : decimal(18)
    + MiscMargin2 : decimal(18)
    + LaborCost : decimal(18)
    + LaborPrice : decimal(18)
    + LaborMargin : decimal(18)
    + Cost : decimal(18)
    + Price : decimal(18)
    + Margin : decimal(18)
    + Cost2 : decimal(18)
    + Price2 : decimal(18)
    + Margin2 : decimal(18)
    + mCost : decimal(18)
    + mMargin : decimal(18)
    + mPrice : decimal(18)
    + mMetalCost : decimal(18)
    + mMetalMargin : decimal(18)
    + mMetalPrice : decimal(18)
    + mStoneCost : decimal(18)
    + mStoneMargin : decimal(18)
    + mStonePrice : decimal(18)
    + mLaborCost : decimal(18)
    + mLaborMargin : decimal(18)
    + mLaborPrice : decimal(18)
    + mPartsCost : decimal(18)
    + mPartsMargin : decimal(18)
    + mPartsPrice : decimal(18)
    + mMiscCost : decimal(18)
    + mMiscMargin : decimal(18)
    + mMiscPrice : decimal(18)
    + IntPric : int
}

class ProductCatagories {
    + ProdCatID : char(5) [PK]
    + ProdCatName : varchar(50)
}

class ProductLaborCost {
    + Design : varchar(25) [PK, FK → Products.Design]
    + LaborTypeID : char(3) [PK, FK → LaborTypes.LaborTypeID]
    + LaborCurrID : char(2)
    + LaborCost : decimal(18)
}

class ProductMiscCost {
    + Design : varchar(25) [PK, FK → Products.Design]
    + MiscTypeID : char(3) [PK, FK → MiscTypes.MiscTypeID]
    + MiscCurrID : char(2)
    + MiscCost : decimal(18)
}

class ProductParts {
    + Design : varchar(25) [PK, FK → Products.Design]
    + PartID : varchar(5) [PK, FK → Parts.PartID]
    + Qty : int
}

class Products {
    + Design : varchar(25) [PK]
    + CatID : char(2) [FK → Models.CatID]
    + OrnID : char(5) [FK → Models.OrnID]
    + StoneID : varchar(14)
    + GoldID : varchar(4)
    + Inactive : bit
    + CreateDate : datetime
    + Description : varchar(100)
    + ProdCatID : char(5) [FK → ProductCatagories.ProdCatID]
    + InCollection : bit
    + OrnIDNum : int
}

class Sketches {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + Picture : image
    + Sketch : image
    + LastUpdated : datetime
    + Model : varchar(7)
}

class SketchesOLD {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + Picture : image
}

class SnapShots {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + StoneID : varchar(14)
    + GoldID : varchar(4)
    + Picture : image
    + LastUpdated : datetime
}

class SnapshotsOLD {
    + CatID : char(2) [PK]
    + OrnID : char(5) [PK]
    + StoneID : varchar(14)
    + GoldID : varchar(4)
    + Picture : image
}

class StoneCatagories {
    + StoneCatID : char(1) [PK]
    + StoneCatName : varchar(50)
    + StoneCatName2 : varchar(50)
    + PerChange : decimal(18)
    + DefaulCurrID : char(2)
    + ApplyRecut : bit
    + StoneGroup : char(2)
}

class StoneGrades {
    + MarginID : varchar(5) [PK, FK → Margins.MarginID]
    + StoneCatID : char(1) [PK]
    + StoneGrade : char(2) [PK]
}

class StoneInvWeights {
    + TypeID : char(5) [PK]
    + ShapeID : char(5) [PK]
    + ShadeID : char(5) [PK]
    + StoneSize : varchar(10) [PK]
    + UnitWgt : decimal(18)
}

class StoneLots {
    + TypeID : char(5) [PK, FK → StoneTypes.TypeID]
    + ShapeID : char(5) [PK, FK → StoneShapes.ShapeID]
    + ShadeID : char(5) [PK, FK → StoneShades.ShadeID]
    + StoneSize : varchar(10) [PK, FK → StoneSizes.StoneSize]
    + Grade : char(2) [PK, FK → Grades.Grade]
    + UnitCost : decimal(18)
    + StoneUCostCurrID : char(2)
    + Item : varchar(30)
}

class StoneMargins {
    + MarginID : varchar(5) [PK, FK → Margins.MarginID]
    + StoneCatID : char(1) [PK]
    + TypeID : char(5) [PK, FK → StoneTypes.TypeID]
    + ShapeID : char(5) [PK, FK → StoneShapes.ShapeID]
    + StoneSize : varchar(10) [PK, FK → StoneSizes.StoneSize]
    + ShadeID : char(5) [PK, FK → StoneShades.ShadeID]
    + StoneMargin : decimal(18)
}

class StoneMarginsConditional {
    + MarginID : varchar(5) [PK, FK → Margins.MarginID]
    + StoneCatID : char(1) [PK]
    + Condition : char(2) [PK]
    + Amount : decimal(18)
    + CurrID : char(2)
    + StoneMargin : decimal(18)
}

class StoneSettingCost {
    + SetID : smallint [PK, FK → StoneSettings.SetID]
    + TypeID : char(5) [PK, FK → StoneTypes.TypeID]
    + SetUnitCost : decimal(18)
    + SetCostCurrID : char(2)
}

class StoneSettings {
    + SetID : smallint [PK]
    + SetName : varchar(50)
    + SetName2 : varchar(50)
}

class StoneShades {
    + ShadeID : char(5) [PK]
    + ShadeName : varchar(25)
    + ShadeName2 : varchar(50)
}

class StoneShapes {
    + ShapeID : char(5) [PK]
    + ShapeName : varchar(20)
    + ShapeName2 : varchar(20)
}

class StoneSizes {
    + StoneSize : varchar(10) [PK]
}

class StoneTypes {
    + TypeID : char(5) [PK]
    + TypeName : varchar(20)
    + TypeName2 : varchar(20)
    + StoneCatID : char(1) [FK → StoneCatagories.StoneCatID]
    + WgtMultiplier : decimal(18)
}

class StoneWeights {
    + TypeID : char(5) [PK, FK → StoneTypes.TypeID]
    + ShapeID : char(5) [PK, FK → StoneShapes.ShapeID]
    + ShadeID : char(5) [PK, FK → StoneShades.ShadeID]
    + StoneSize : varchar(10) [PK, FK → StoneSizes.StoneSize]
    + UnitWgt : decimal(18)
    + InvWgt : decimal(18)
}

class VarSetting {
    + setting_min_cost : float
    + filling_min_cost : float
}

'-- Views Definitions -- (Attributes only; no PK/FK relationships) --

class vwMFSJewelry {
    + Item : varchar(31)
    + ItemClass : varchar(7)
    + Source : varchar(4)
    + ItemCat : varchar(25)
    + ItemDescr : varchar(1)
    + ItemSize : varchar(1)
    + MetalType : varchar(50)
    + MetalColor : varchar(1)
    + Purity : char(5)
    + StoneTypeID : varchar(1)
    + StoneShapeID : varchar(1)
    + StoneShadeID : varchar(1)
    + StoneGrade : varchar(1)
    + Inactive : bit
    + CurrID : varchar(2)
    + Qty : bit
    + Weight : bit
    + WgtUnit : varchar(3)
    + CostON : varchar(1)
    + Lot : bit
    + SuppItemRef : varchar(1)
    + CustItemRef : varchar(1)
    + BarCode : varchar(1)
    + PicRef : varchar(7)
}

class vwMFSJewelryPart {
    + Item : varchar(33)
    + Comp : varchar(18)
    + Qty : int
    + QtyUnit : varchar(3)
    + Weight : decimal(38)
    + WgtUnit : varchar(3)
    + LaborDescr : varchar(1)
    + LaborRate : int
    + LaborCurrID : varchar(2)
}

class vwMFSJewelryPart01 {
    + Comp : varchar(19)
    + Qty : int
    + QtyUnit : varchar(3)
    + Weight : decimal(38)
    + WgtUnit : varchar(3)
    + LaborDescr : varchar(1)
    + LaborRate : int
    + LaborCurrID : varchar(2)
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID2 : char(5)
    + Purity2 : char(5)
}

class vwMFSJewelryStone {
    + Item : varchar(31)
    + Comp : varchar(27)
    + Qty : smallint
    + QtyUnit : varchar(3)
    + Weight : decimal(18)
    + WgtUnit : varchar(3)
    + LaborDescr : varchar(50)
    + LaborRate : int
    + LaborCurrID : varchar(2)
}

class vwMFSJewelryStone01 {
    + Item : varchar(31)
    + Comp : varchar(30)
    + Qty : smallint
    + QtyUnit : varchar(3)
    + Weight2 : decimal(18)
    + WgtUnit : varchar(3)
    + LaborDescr : varchar(50)
    + LaborRate : int
    + LaborCurrID : varchar(2)
}

class vwMFSPartComps {
    + Item : varchar(19)
    + Comp : varchar(11)
    + Qty : int
    + QtyUnit : varchar(3)
    + Weight : decimal(18)
    + WgtUnit : varchar(3)
    + LaborDescr : varchar(1)
    + LaborRate : int
    + LaborCurrID : varchar(2)
}

class vwMFSParts {
    + Item : varchar(19)
    + ItemClass : varchar(4)
    + Source : varchar(4)
    + ItemCat : varchar(25)
    + ItemDescr : varchar(1)
    + ItemSize : varchar(1)
    + MetalType : varchar(50)
    + MetalColor : varchar(1)
    + Purity : char(5)
    + StoneTypeID : varchar(1)
    + StoneShapeID : varchar(1)
    + StoneShadeID : varchar(1)
    + StoneGrade : varchar(1)
    + Inactive : bit
    + CurrID : varchar(2)
    + Qty : bit
    + Weight : bit
    + WgtUnit : varchar(3)
    + CostON : varchar(1)
    + Lot : bit
    + SuppItemRef : varchar(1)
    + CustItemRef : varchar(1)
    + BarCode : varchar(1)
    + PicRef : varchar(7)
}

class vwMFSPurchParts {
    + Item : varchar(11)
    + ItemClass : varchar(11)
    + Source : varchar(3)
    + ItemCat : varchar(1)
    + ItemDescr : varchar(20)
    + ItemSize : varchar(1)
    + MetalType : varchar(1)
    + MetalColor : varchar(1)
    + Purity : char(5)
    + StoneTypeID : varchar(1)
    + StoneShapeID : varchar(1)
    + StoneShadeID : varchar(1)
    + StoneGrade : varchar(1)
    + Inactive : int
    + CurrID : varchar(2)
    + Qty : int
    + Weight : int
    + WgtUnit : varchar(3)
    + CostOn : varchar(1)
    + Lot : int
    + SuppItemRef : varchar(1)
    + CustItemRef : varchar(1)
    + BarCode : varchar(1)
    + PicRef : varchar(1)
}

class vwMFSSilverMold {
    + Item : varchar(7)
    + ItemClass : varchar(11)
    + Source : varchar(4)
    + ItemCat : varchar(25)
    + ItemDescr : varchar(1)
    + ItemSize : varchar(1)
    + MetalType : varchar(6)
    + MetalColor : varchar(1)
    + Purity : varchar(3)
    + StoneTypeID : varchar(1)
    + StoneShapeID : varchar(1)
    + StoneShadeID : varchar(1)
    + StoneGrade : varchar(1)
    + Inactive : bit
    + CurrID : varchar(2)
    + Qty : bit
    + Weight : bit
    + WgtUnit : varchar(3)
    + CostON : varchar(1)
    + Lot : bit
    + SuppItemRef : varchar(1)
    + CustItemRef : varchar(1)
    + BarCode : varchar(1)
    + PicRef : varchar(7)
}

class vwMFSStones {
    + Item : varchar(27)
    + ItemClass : varchar(5)
    + Source : varchar(3)
    + ItemCat : varchar(50)
    + ItemDescr : varchar(255)
    + ItemSize : varchar(10)
    + MetalType : varchar(1)
    + MetalColor : varchar(1)
    + Purity : varchar(1)
    + TypeID : char(5)
    + ShapeID : char(5)
    + ShadeID : char(5)
    + StoneGrade : char(2)
    + Inactive : bit
    + CurrID : varchar(2)
    + Qty : bit
    + Weight : bit
    + WgtUnit : varchar(3)
    + CostON : varchar(1)
    + Lot : bit
    + SuppItemRef : varchar(1)
    + CustItemRef : varchar(1)
    + BarCode : varchar(1)
    + PicRef : varchar(1)
}

class vwModelLaborPrice {
    + MarginID : varchar(5)
    + LaborMargin : decimal(18)
    + Design : varchar(25)
    + LaborTypeID : varchar(3)
    + LaborCost : decimal(21)
    + LaborConvCost : decimal(18)
    + LaborCurrID : char(2)
    + LaborPrice : decimal(37)
    + LaborPriceCurrID : char(2)
}

class vwModelMetalConv {
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID : varchar(4)
    + MetalID : char(2)
    + Purity : char(5)
    + Weight : decimal(18)
    + MetalID2 : char(5)
    + Purity2 : char(5)
    + Weight2 : decimal(18)
    + MetalConvto : char(2)
    + GoldID2 : char(5)
}

class vwModelMetalCost {
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID : varchar(4)
    + MetalID : char(2)
    + Purity : char(5)
    + Weight : decimal(18)
    + MetalID2 : char(5)
    + Purity2 : char(5)
    + Weight2 : decimal(18)
    + MetalConvto : char(2)
    + GoldID2 : char(5)
    + MetalUnitCost : decimal(18)
    + MetalCost : decimal(38)
    + MetalCurr : char(2)
}

class vwModelStone {
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + TypeID : char(5)
    + SetID : smallint
    + ShapeID : char(5)
    + StoneSize : varchar(10)
    + ShadeID : char(5)
    + Pcs : smallint
    + Weight : decimal(18)
    + StoneUnitCost : decimal(18)
    + StoneCost : decimal(18)
    + StoneCostCurrID : char(2)
    + SetUnitCost : decimal(18)
    + SetCost : decimal(18)
    + SetCostCurrID : char(2)
    + ShapeID2 : char(5)
    + StoneSize2 : varchar(10)
    + Weight2 : decimal(18)
}

class vwModelStoneCost {
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + StoneCatID : char(1)
    + TypeID : char(5)
    + ShapeID : char(5)
    + StoneSize : varchar(10)
    + ShadeID : char(5)
    + Pcs : smallint
    + Weight : decimal(18)
    + Grade : char(2)
    + StoneUCost : decimal(18)
    + StoneUCostCurrID : char(2)
    + StoneCost : decimal(18)
    + StoneCostCurrID : char(2)
    + SetID : smallint
    + SetUnitCost : decimal(18)
    + SetCost : decimal(24)
    + RecutCost : decimal(24)
    + ShapeID2 : char(5)
    + StoneSize2 : varchar(30)
}

class vwModelStoneTypeSum {
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + TypeID : char(5)
    + TypeName : varchar(20)
    + Pcs : int
    + PurWgt : decimal(38)
    + InvWgt : decimal(38)
}

class vwModelStoneWeights {
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + StoneGroup : char(2)
    + StoneCatID : char(1)
    + StoneCatName : varchar(50)
    + TypeID : char(5)
    + TypeName : varchar(20)
    + ShapeID : char(5)
    + ShapeName : varchar(20)
    + StoneSize : varchar(10)
    + ShadeID : char(5)
    + ShadeName : varchar(25)
    + Pcs : smallint
    + PurUWgt : decimal(18)
    + PurWgt : decimal(24)
    + ShapeID2 : char(5)
    + ShapeName2 : varchar(20)
    + StoneSize2 : varchar(10)
    + InvUWgt : decimal(18)
    + InvWgt : decimal(24)
    + LotName : varchar(30)
    + LotName2 : varchar(30)
}

class vwModelStoneWeightsGroupSum {
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + StoneGroup : char(2)
    + Pcs : int
    + PurWgt : decimal(38)
    + InvWgt : decimal(38)
}

class vwPrice {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + GoldID : varchar(4)
    + GoldID2 : char(5)
    + MetalConvto : char(2)
    + Purity2 : char(5)
    + MetalTWeight : decimal(38)
    + MetalTConvWeight : decimal(38)
    + MetalTCost : decimal(38)
    + MetalTPrice : decimal(38)
    + MetalTMargin : decimal(38)
    + Currency : char(2)
    + Expr1 : decimal(38)
    + Expr2 : decimal(38)
    + Expr3 : decimal(38)
    + Expr4 : decimal(38)
    + Expr5 : decimal(38)
    + Expr6 : decimal(38)
    + Expr7 : decimal(38)
    + Expr8 : decimal(38)
    + Expr9 : decimal(38)
    + Expr10 : decimal(38)
    + Expr11 : decimal(38)
    + Expr12 : decimal(38)
}

class vwPriceList {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + Design2 : varchar(25)
    + Purity : char(5)
    + Currency : char(2)
    + MetalConvto : char(2)
    + MetalCost : decimal(38)
    + MetalPrice : decimal(38)
    + MetalMargin : decimal(38)
    + StoneCost : decimal(38)
    + StonePrice : decimal(38)
    + StoneMargin : decimal(38)
    + PartsCost : decimal(38)
    + PartsPrice : decimal(38)
    + PartsMargin : decimal(38)
    + MiscCost : decimal(38)
    + MiscPrice : decimal(38)
    + MiscMargin : decimal(38)
    + LaborCost : decimal(38)
    + LaborPrice : decimal(38)
    + LabotMargin : decimal(38)
    + Cost : decimal(38)
    + Price : decimal(38)
    + Margin : decimal(38)
}

class vwPriceParameters {
    + MarginID : varchar(5)
    + Purity : char(5)
    + MetalID : char(2)
    + Design : varchar(25)
    + CountryID : char(2)
}

class vwProdLaborPrice {
    + MarginID : varchar(5)
    + LaborMargin : decimal(18)
    + Design : varchar(25)
    + LaborTypeID : char(3)
    + LaborCost : decimal(21)
    + LaborConvCost : decimal(18)
    + LaborCurrID : char(2)
    + LaborPrice : decimal(37)
    + LaborPriceCurrID : char(2)
}

class vwProdLaborPrice00 {
    + MarginID : varchar(5)
    + LaborMargin : decimal(18)
    + Design : varchar(25)
    + LaborTypeID : char(3)
    + LaborCost : decimal(18)
    + LaborConvCost : decimal(18)
    + LaborCurrID : char(2)
    + LaborPrice : decimal(37)
    + LaborPriceCurrID : char(2)
}

class vwProdLaborPriceSum {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + LaborTCost : decimal(38)
    + LaborTPrice : decimal(38)
    + LaborTMargin : decimal(38)
    + Currency : char(2)
}

class vwProdMetalPrice {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + StoneID : varchar(14)
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID : varchar(4)
    + MetalID : char(2)
    + Purity : char(5)
    + Weight : decimal(18)
    + MetalID2 : char(5)
    + Purity2 : char(5)
    + Weight2 : decimal(18)
    + MetalConvto : char(2)
    + GoldID2 : char(5)
    + MetalUnitCost : decimal(18)
    + MetalCost : decimal(38)
    + MetalCurr : char(2)
    + MetalMargin : decimal(10)
    + MetalPrice : decimal(38)
}

class vwProdMetalPriceSum {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + GoldID : varchar(4)
    + MetalConvto : char(2)
    + Purity2 : char(5)
    + MetalTWeight : decimal(38)
    + MetalTConvWeight : decimal(38)
    + MetalTCost : decimal(38)
    + MetalTPrice : decimal(38)
    + MetalTMargin : decimal(38)
    + Currency : char(2)
}

class vwProdMiscPrice {
    + MarginID : varchar(5)
    + MiscMargin : decimal(10)
    + Design : varchar(25)
    + MiscTypeID : char(3)
    + MiscCost : decimal(18)
    + MiscConvCost : decimal(18)
    + MiscCurrID : char(2)
    + MiscPrice : decimal(29)
    + MiscPriceCurrID : char(2)
    + OverAllMargin : decimal(18)
}

class vwProdMiscPriceSum {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + MiscTCost : decimal(38)
    + MiscTPrice : decimal(38)
    + MiscTMargin : decimal(38)
    + Currency : char(2)
    + OverAllMargin : decimal(18)
}

class vwProdPartPrice {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + PartID : varchar(5)
    + Qty : int
    + Purity : char(5)
    + PartUCost : decimal(18)
    + PartUCostCurrID : char(2)
    + PartCost : decimal(29)
    + PartsConvCost : decimal(18)
    + PartsMargin : decimal(18)
    + PartPrice : decimal(18)
    + PartPriceCurrID : char(2)
}

class vwProdPartsPriceSum {
    + MarginID : varchar(5)
    + Design : varchar(25)
    + Purity : char(5)
    + PartsTCost : decimal(38)
    + PartsTPrice : decimal(38)
    + PartsTMargin : decimal(38)
    + Currency : char(2)
}

class vwProdStonePrice {
    + MarginID : varchar(5)
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + StoneCatID : char(1)
    + TypeID : char(5)
    + ShapeID : char(5)
    + StoneSize : varchar(10)
    + ShadeID : char(5)
    + Pcs : smallint
    + Weight : decimal(18)
    + Grade : char(2)
    + StoneUCost : decimal(18)
    + StoneUCostCurrID : char(2)
    + StoneCost : decimal(18)
    + StoneCostCurrID : char(2)
    + SetID : smallint
    + SetUnitCost : decimal(18)
    + SetCost : decimal(24)
    + RecutCost : decimal(18)
    + ShapeID2 : char(5)
    + StoneSize2 : varchar(30)
    + StoneMargin : decimal(10)
    + StonePrice : decimal(29)
    + SetMargin : decimal(18)
    + SetPrice : decimal(38)
    + RecutPrice : decimal(37)
    + StoneLaborPrice : decimal(38)
}

class vwProdStonePriceSum {
    + MarginID : varchar(5)
    + CatID : char(2)
    + OrnID : char(5)
    + StoneID : varchar(14)
    + StoneTCost : decimal(38)
    + StoneTPrice : decimal(38)
    + StoneTMargin : decimal(38)
    + SetTCost : decimal(38)
    + SetTPrice : decimal(38)
    + SetTMargin : decimal(38)
    + Currency : char(2)
    + Grade : char(2)
    + RecutTCost : decimal(38)
    + RecutTMargin : decimal(38)
    + RecutTPrice : decimal(38)
    + StoneLaborTCost : decimal(38)
    + StoneLaborTMargin : decimal(38)
    + StoneLaborTPrice : decimal(38)
}

class vwProductPrices {
    + legacy_reference : varchar(25)
    + EM+10 : numeric(18)
    + EM+15 : numeric(18)
    + EM+70 : numeric(18)
    + EM+77 : numeric(18)
    + EMA : numeric(18)
    + N35 : numeric(18)
    + NET : numeric(18)
    + NR+10 : numeric(18)
    + NRET : numeric(18)
    + ORET : numeric(18)
    + UK : numeric(18)
    + W10 : numeric(18)
    + W15 : numeric(18)
}

class vwSpareParts {
    + Design : varchar(25)
    + PartName : varchar(20)
    + PartID : varchar(5)
    + Qty : int
}

class vwStoneLots {
    + StoneCatID : char(1)
    + StoneCatName : varchar(50)
    + TypeID : char(5)
    + TypeName : varchar(20)
    + ShapeID : char(5)
    + ShapeName : varchar(20)
    + ShadeID : char(5)
    + ShadeName : varchar(25)
    + StoneSize : varchar(10)
    + Grade : char(2)
    + UnitCost : decimal(18)
    + StoneUCostCurrID : char(2)
    + CurrName : varchar(15)
}

class vwStonePrices {
    + MarginID : varchar(5)
    + TypeID : char(5)
    + ShadeID : char(5)
    + ShapeID : char(5)
    + StoneSize : varchar(10)
    + UnitCost : decimal(18)
    + Margin : decimal(10)
    + Price : decimal(29)
    + StoneUCostCurrID : char(2)
}

class vwTEmp {
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID : varchar(4)
    + Labor : decimal(18)
    + Casting : decimal(18)
    + Filing : decimal(18)
    + Polishing : decimal(18)
    + TotLabor : decimal(21)
    + LaborCurrID : char(2)
}

class vwTempDupLabor1 {
    + CatID : char(2)
    + OrnID : char(5)
    + GoldID : varchar(4)
    + LaborTypeID : char(3)
    + Cost : decimal(38)
    + LaborCurrID : char(2)
}

' =========================
' Relationships (Foreign Keys)
' =========================

MatchingModels .down.> Models       : CatID\nOrnID
MetalConv .down.> Metals            : MetalID
MetalMargins .down.> Margins        : MarginID
MetalMargins .down.> MetalPurities  : Purity
MetalPurityConv .down.> MetalPurities : Purity
MiscMargins .down.> MiscTypes       : MiscTypeID
MiscMargins .down.> Margins         : MarginID
ModelMetal .down.> Models           : CatID\nOrnID
ModelMetal .down.> Metals           : MetalID
ModelMetal .down.> MetalPurities    : Purity
ModelStone .down.> Models           : CatID\nOrnID
ModelStone .down.> StoneTypes       : TypeID
ModelStone .down.> StoneSettings    : SetID
ModelStone .down.> StoneShapes      : ShapeID
ModelStone .down.> StoneSizes       : StoneSize
ModelStone .down.> StoneShades      : ShadeID
PartsCost .down.> Parts             : PartID
PartsCost .down.> MetalPurities     : Purity
ProductLaborCost .down.> Products   : Design
ProductLaborCost .down.> LaborTypes  : LaborTypeID
ProductMiscCost .down.> Products    : Design
ProductMiscCost .down.> MiscTypes    : MiscTypeID
ProductParts .down.> Products       : Design
ProductParts .down.> Parts          : PartID
Products .down.> Models             : CatID\nOrnID
Products .down.> ProductCatagories  : ProdCatID
StoneGrades .down.> Margins         : MarginID
StoneLots .down.> StoneTypes        : TypeID
StoneLots .down.> StoneShapes       : ShapeID
StoneLots .down.> StoneShades       : ShadeID
StoneLots .down.> StoneSizes        : StoneSize
StoneLots .down.> Grades            : Grade
StoneMargins .down.> Margins        : MarginID
StoneMargins .down.> StoneTypes     : TypeID
StoneMargins .down.> StoneShapes    : ShapeID
StoneMargins .down.> StoneSizes     : StoneSize
StoneMargins .down.> StoneShades    : ShadeID
StoneMarginsConditional .down.> Margins      : MarginID
StoneSettingCost .down.> StoneSettings    : SetID
StoneSettingCost .down.> StoneTypes       : TypeID
StoneTypes .down.> StoneCatagories  : StoneCatID
StoneWeights .down.> StoneTypes     : TypeID
StoneWeights .down.> StoneShapes    : ShapeID
StoneWeights .down.> StoneShades    : ShadeID
StoneWeights .down.> StoneSizes     : StoneSize

@enduml

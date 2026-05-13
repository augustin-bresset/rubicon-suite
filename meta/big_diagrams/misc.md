
class CompanyInfo {
  +RowNum : int
  AccNumberLine1 : varchar(255)
  AccNumberLine2 : varchar(255)
}


class Currencies {
  +CountryID : char(2)
  CountryName : varchar(50)
  LangName : varchar(50)
  CurrName : varchar(15)
  BaseCountry : tinyint
  Rate : decimal(18, ?)
}


class Sketches {
  CatID : char(2)
  OrnID : char(5)
  Picture : image
  Sketch : image
  LastUpdated : datetime
  Model : varchar(7)
}


class SnapShots {
  CatID : char(2)
  OrnID : char(5)
  StoneID : varchar(14)
  GoldID : varchar(4)
  Picture : image
  LastUpdated : datetime
}
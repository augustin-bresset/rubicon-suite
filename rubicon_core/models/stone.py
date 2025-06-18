# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class StoneCategory(Base):
    __tablename__ = "stone_catagories"
    category_id   = Column(CHAR(1), primary_key=True)      # CHAR(1)
    name          = Column(String(50), nullable=False)
    
    types = relationship("StoneType", back_populates="category")

class StoneType(Base):
    __tablename__ = "stone_types"
    type_id       = Column(CHAR(5), primary_key=True)       # CHAR(5)
    type_name     = Column(String(20), nullable=False)
    category_id   = Column(CHAR(1), ForeignKey("stone_catagories.category_id"), nullable=False)
    density       = Column(Numeric(10, 3), doc="Density in kg/m3") 
    
    category      = relationship("StoneCategory", back_populates="types")
    stones        = relationship("Stone", back_populates="stone_type")

class StoneShape(Base):
    __tablename__ = "stone_shapes"
    shape      = Column(CHAR(5), primary_key=True)
    description    = Column(String(20))

class StoneSize(Base):
    __tablename__ = "stone_sizes"
    size        = Column(String(10), primary_key=True)
    description = Column(String(20))

class StoneShade(Base):
    __tablename__ = "stone_shades"
    shade        = Column(CHAR(5), primary_key=True)
    description  = Column(String(25), nullable=False)
    
class Stone(Base):
    __tablename__ = "stone"
    
    stone_id    = Column(Integer, primary_key=True)
    type_id     = Column(CHAR(5), ForeignKey("stone_types.type_id"), nullable=False)
    shape       = Column(CHAR(5), ForeignKey("stone_shapes.shape"), nullable=False)
    shade       = Column(CHAR(5), ForeignKey("stone_shades.shade"), nullable=False)
    size        = Column(String(10), ForeignKey("stone_sizes.size"), nullable=False)
    weight      = Column(Numeric(5, 2), doc="Weight in carat (=0.2g)")
    cost        = Column(Numeric(10, 2), nullable=False)
    currency    = Column(CHAR(3), ForeignKey("misc_currency.code"), nullable=False)
    item_id    = Column(String(40), ForeignKey("stock.item_id"))
    stone_type  = relationship("StoneType", back_populates="stones")

    stone_size  = relationship("StoneSize")
    stone_shape = relationship("StoneShape")
    stone_shade = relationship("StoneShade")




class StoneLotCost(Base):
    __tablename__ = "stone_lot_cost"   
     
    stone_id    = Column(Integer, ForeignKey("stone.stone_id"), nullable=False)
    quantity    = Column(Integer, nullable=False)
    
    
class StoneSetting(Base):
    __tablename__ = "stone_settings"
    setid        = Column(SmallInteger, primary_key=True)
    setname      = Column(String(50), nullable=False)

class StoneSettingCost(Base):
    __tablename__ = "stone_setting_cost"
    setid        = Column(SmallInteger, ForeignKey("stone_settings.setid"), primary_key=True)
    typeid       = Column(CHAR(5), ForeignKey("stone_types.typeid"), primary_key=True)
    unit_cost    = Column(Numeric(18), nullable=False)
    
    setting_ref  = relationship("StoneSetting")
    type_ref     = relationship("StoneType")

class StoneMargin(Base):
    __tablename__ = "stone_margins"
    marginid     = Column(String(5), primary_key=True)
    stonecatid   = Column(CHAR(1), primary_key=True)
    typeid       = Column(CHAR(5), primary_key=True)
    shapeid      = Column(CHAR(5), primary_key=True)
    stonesize    = Column(String(10), primary_key=True)
    shadeid      = Column(CHAR(5), primary_key=True)
    stone_margin = Column(Numeric(18), nullable=False)

    category     = relationship("StoneCategory", back_populates="margins")

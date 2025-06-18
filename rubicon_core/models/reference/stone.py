# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

from ..transaction.stone import Stone
from ..transaction.stock import Item

class StoneCategory(Base):
    __tablename__ = "stone_categories"
    id      = Column(CHAR(1), primary_key=True)      # CHAR(1)
    name    = Column(String(50), nullable=False)
    
    types = relationship("StoneType", back_populates="category")

class StoneType(Base):
    __tablename__ = "stone_types"
    
    category_id   = Column(CHAR(1), ForeignKey("stone_categories.id"), nullable=False)
    
    id            = Column(CHAR(5), primary_key=True)       # CHAR(5)
    type_name     = Column(String(20), nullable=False)
    density       = Column(Numeric(10, 3), doc="Density in kg/m3") 
    
    category      = relationship("StoneCategory", back_populates="types")
    stones        = relationship("Stone", back_populates="stone_type")

class StoneShape(Base):
    __tablename__ = "stone_shapes"
    
    shape          = Column(CHAR(5), primary_key=True)
    description    = Column(String(20))

class StoneSize(Base):
    __tablename__ = "stone_sizes"
    
    size        = Column(String(10), primary_key=True)
    description = Column(String(20))

class StoneShade(Base):
    __tablename__ = "stone_shades"
    
    shade        = Column(CHAR(5), primary_key=True)
    description  = Column(String(25), nullable=False)
    
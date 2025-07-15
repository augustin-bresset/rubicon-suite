# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


class StoneCategory(Base):
    __tablename__ = "stone_categories"
    
    id            = Column(Integer, primary_key=True, autoincrement=True)      
    code          = Column(CHAR(1), nullable=False, unique=True)
    name          = Column(String(50), nullable=False)
    
    types = relationship("StoneType", back_populates="category")

class StoneType(Base):
    __tablename__ = "stone_types"
    
    category_id   = Column(Integer, ForeignKey("stone_categories.id"), nullable=False)
    
    id            = Column(Integer, primary_key=True, autoincrement=True)      
    code          = Column(CHAR(5), nullable=False, unique=True)
    name          = Column(String(20), nullable=False)
    density       = Column(Numeric(10, 3), doc="Density in g/cm3") 

    category      = relationship("StoneCategory", back_populates="types")
    stones        = relationship("Stone", back_populates="stone_type")


class StoneSize(Base):
    __tablename__ = "stone_sizes"
    
    size         = Column(String(10), primary_key=True)

class StoneShape(Base):
    __tablename__ = "stone_shapes"
    
    id            = Column(Integer, primary_key=True, autoincrement=True)
    code          = Column(CHAR(5), nullable=False, unique=True)
    name          = Column(String(20))

class StoneShade(Base):
    __tablename__ = "stone_shades"
    
    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(CHAR(5), nullable=False, unique=True)
    name        = Column(String(25), nullable=False)
    
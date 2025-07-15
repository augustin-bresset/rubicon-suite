# rubicon_core/models/misc.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


class Currency(Base):
    __tablename__ = "currencies"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(CHAR(3), nullable=False, unique=True)   # ex. "EUR", "USD"
    name        = Column(String(50), nullable=False)  # "Euro", "US Dollar"
    symbol      = Column(String(5), nullable=True)    # "€", "$"
    
class Region(Base):
    __tablename__ = "regions"
    
    id      = Column(Integer, primary_key=True, autoincrement=True)
    code    = Column(CHAR(2), nullable=False, unique=True)
    name    = Column(String(40), nullable=False)
    
    countries = relationship("Country")
    
class Country(Base):
    __tablename__ = "countries"
    
    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(CHAR(2), nullable=False, unique=True)
    name        = Column(String(40), nullable=False)
    region_id   = Column(Integer, ForeignKey("regions.id"))
    
    region = relationship("Region", back_populates="countries")
    
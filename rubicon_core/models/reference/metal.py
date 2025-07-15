# rubicon_core/models/metal.py

from sqlalchemy import (
    Column, Integer, String, Numeric, CHAR, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


class Metal(Base):
    __tablename__ = "metals"
    
    id             = Column(Integer, primary_key=True, autoincrement=True)
    code           = Column(CHAR(2), nullable=False, unique=True)
    name           = Column(String(50), nullable=False)    
    unit_cost      = Column(Numeric(18), nullable=False, doc="Cost per kg")
    currency       = Column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    plating        = Column(Boolean, nullable=True)         # BIT

    is_gold        = Column(Boolean, default=True)
    purity         = Column(String(3), ForeignKey("gold_purities.name"), default=None)

    is_reference   = Column(Boolean, default=False, doc="True for With Gold 18K")
    
    
    
class GoldPurity(Base):
    __tablename__ = "gold_purities"
    
    id       = Column(Integer, primary_key=True, autoincrement=True)
    name     = Column(String(3), nullable=False, unique=True)
    percent  = Column(Numeric(4, 1))



# rubicon_core/models/metal.py

from sqlalchemy import (
    Column, Integer, String, Numeric, CHAR, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


class Metal(Base):
    __tablename__ = "metals"
    
    id       = Column(CHAR(2), primary_key=True)
    name     = Column(String(50), nullable=False)    
    ucost    = Column(Numeric(18), nullable=False, doc="Cost per kg")
    currency       = Column(Column(CHAR(3), "currencies.code"), nullable=False, default="USD")
    apply_plating  = Column(Boolean, nullable=True)         # BIT

    is_gold        = Column(Boolean, default=True)
    purity         = Column(String(3), ForeignKey("gold_purities.name"), default=None)

    is_reference   = Column(Boolean, default=False, doc="True for With Gold 18K")
    
    
    
class GoldPurity(Base):
    __tablename__ = "gold_purities"
    
    name     = Column(String(3), primary_key=True)
    percent  = Column(Numeric(3, 1))



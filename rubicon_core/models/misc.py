# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


# rubicon_core/models/currency.py
class Currency(Base):
    __tablename__ = "currencies"
    code        = Column(CHAR(3), primary_key=True)   # ex. "EUR", "USD"
    name        = Column(String(50), nullable=False)  # "Euro", "US Dollar"
    symbol      = Column(String(5), nullable=True)    # "€", "$"

# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


# rubicon_core/models/currency.py
class Stock(Base):
    __tablename__ = "stock"
    item_id = Column(String(40), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    
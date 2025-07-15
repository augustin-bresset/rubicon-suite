# rubicon_core/models/item.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class Item(Base):
    __tablename__ = "items"
    
    id       = Column(Integer, primary_key=True, autoincrement=True)
    code     = Column(String(40), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False, default=1)
    
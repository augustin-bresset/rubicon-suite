from sqlalchemy import (
    Column, CHAR, String, Numeric, ForeignKey,
    Boolean, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class Margin(Base):
    __tablename__ = "margins"
    
    id          = Column(String(10), primary_key=True)
    name        = Column(String(40), nullable=False)
    percent     = Column(Numeric(5, 2), nullable=False)
    
    is_active   = Column(Boolean, default=True)
    
    
class MiscMargin(Base):
    __tablename__ = "margin_miscs"
    
    id      = Column(Integer, primary_key=True, autoincrement=True)
    type    = Column(String(20), nullable=False)
    ratio   = Column(Numeric(6, 4), nullable=False)
    


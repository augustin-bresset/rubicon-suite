# rubicon_core/models/stone.py

from sqlalchemy import (
    Table, Column, CHAR, String, Numeric, SmallInteger, ForeignKey, Boolean, Integer
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base


class Stone(Base):
    __tablename__ = "stones"
    
    type_id     = Column(CHAR(5), ForeignKey("stone_types.id"), nullable=False)
    
    id    = Column(Integer, primary_key=True)
    shape       = Column(CHAR(5), ForeignKey("stone_shapes.shape"), nullable=False)
    shade       = Column(CHAR(5), ForeignKey("stone_shades.shade"), nullable=False)
    size        = Column(String(10), ForeignKey("stone_sizes.size"), nullable=False)
    weight      = Column(Numeric(5, 2), doc="Weight in carat (=0.2g)")
    cost        = Column(Numeric(10, 2), nullable=False)
    currency    = Column(CHAR(3), ForeignKey("currencies.code"), nullable=False, default="USD")
    item_id    = Column(String(40), ForeignKey("items.id"))
    
    stone_type  = relationship("StoneType", back_populates="stones")

    stone_size  = relationship("StoneSize")
    stone_shape = relationship("StoneShape")
    stone_shade = relationship("StoneShade")


class StoneLot(Base):
    __tablename__ = "stone_lot_cost"   
    
    id          = Column(Integer, primary_key=True, autoincrement=True) 
    stone_id    = Column(Integer, ForeignKey("stones.id"), nullable=False)
    quantity    = Column(Integer, nullable=False)
    
    stone    = relationship("Stone")
    
    
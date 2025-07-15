from sqlalchemy import (
    Column, CHAR, String, Numeric, ForeignKey,
    Boolean, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class Part(Base):
    __tablename__ = "parts"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    code         = Column(CHAR(5), nullable=False, unique=True)
    name         = Column(String(50), nullable=False, unique=True)

    costs   = relationship(
        "PartCost",
        back_populates="part",
        cascade="all, delete-orphan"
    )


class PartCost(Base):
    __tablename__   = "part_costs"
    
    id           = Column(Integer, primary_key=True, autoincrement=True)
    part_id      = Column(Integer, ForeignKey("parts.id"))
    purity_id    = Column(Integer, ForeignKey("gold_purities.id"), nullable=False, 
                          doc="Gold purity 18K, ...")
    
    cost         = Column(Numeric(10, 2), nullable=False, doc="Unit Cost")
    currency_code= Column(
        CHAR(3),
        ForeignKey("currencies.code"),
        nullable=False,
        default="USD"
    )

    part         = relationship("Part", back_populates="costs")
    purity       = relationship("GoldPurity")

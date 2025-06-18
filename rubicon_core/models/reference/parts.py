from sqlalchemy import (
    Column, CHAR, String, Numeric, ForeignKey,
    Boolean, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class Part(Base):
    __tablename__ = "parts"

    id      = Column(CHAR(5), primary_key=True)
    name    = Column(String(50), nullable=False, unique=True)
    is_gold = Column(Boolean, nullable=False, default=True)

    # Tous les coûts selon pureté
    costs   = relationship(
        "PartCost",
        back_populates="part",
        cascade="all, delete-orphan"
    )


class PartCost(Base):
    __tablename__   = "part_costs"
    __table_args__  = (
        UniqueConstraint("part_id", "purity_name", name="uq_part_costs_purity"),
    )

    id           = Column(Integer, primary_key=True, autoincrement=True)
    part_id      = Column(CHAR(5), ForeignKey("parts.id"), nullable=False)
    purity_name  = Column(
        CHAR(3),
        ForeignKey("gold_purities.purity_name"),
        nullable=False,
        doc="Gold purity 18K, ..."
    )
    amount       = Column(Numeric(10, 2), nullable=False, doc="Unit Cost")
    currency_code= Column(
        CHAR(3),
        ForeignKey("currencies.code"),
        nullable=False,
        default="USD"
    )

    part         = relationship("Part", back_populates="costs")
    purity       = relationship("GoldPurity")

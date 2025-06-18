# rubicon_core/models/metal.py

from sqlalchemy import (
    Column, Integer, String, Numeric, CHAR, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from rubicon_core.db import Base

class MetalPurity(Base):
    __tablename__ = "metal_purities"
    # CHAR(5) NOT NULL
    purity      = Column(CHAR(5), primary_key=True)
    purity_per  = Column(Numeric(10,2), nullable=True)     # PRECISION=10

    # reverse « metal_purity_conv », « metal_margins »
    conversions = relationship("MetalPurityConv", back_populates="purity_ref")
    margins     = relationship("MetalMargin", back_populates="purity_ref")

class Metal(Base):
    __tablename__ = "metals"
    metal_id       = Column(CHAR(2), primary_key=True)      # CHAR(2) NOT NULL
    metal_name     = Column(String(50), nullable=False)     # VARCHAR(50)
    metal_ucost    = Column(Numeric(18), nullable=False)
    metal_ucurr_id = Column(CHAR(2), nullable=True)
    apply_plating  = Column(Boolean, nullable=True)         # BIT

    # conversions vers un autre métal
    convs = relationship("MetalConv", back_populates="metal")

class MetalConv(Base):
    __tablename__ = "metal_conv"
    metal_id   = Column(CHAR(2), ForeignKey("metals.metal_id"), primary_key=True)
    metal_id2  = Column(CHAR(2), primary_key=True)
    conv_per   = Column(Numeric(18), nullable=False)

    metal = relationship("Metal", back_populates="convs")

class MetalMargin(Base):
    __tablename__ = "metal_margins"
    margin_id  = Column(String(5), primary_key=True)        # VARCHAR(5)
    prod_catid = Column(CHAR(5), nullable=False)
    purity     = Column(CHAR(5), ForeignKey("metal_purities.purity"), primary_key=True)
    metal_margin = Column(Numeric(18), nullable=True)

    purity_ref = relationship("MetalPurity", back_populates="margins")

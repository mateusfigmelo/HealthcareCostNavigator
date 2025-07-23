"""Procedure model for storing MS-DRG procedure information."""

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Procedure(Base):
    """MS-DRG Procedure model."""

    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(
        String(20), ForeignKey("hospitals.provider_id"), nullable=False
    )
    ms_drg_code = Column(String(10), nullable=False)
    ms_drg_definition = Column(String(500), nullable=False)
    total_discharges = Column(Integer, nullable=False)
    average_covered_charges = Column(Float, nullable=False)
    average_total_payments = Column(Float, nullable=False)
    average_medicare_payments = Column(Float, nullable=False)

    # Relationships
    hospital = relationship("Hospital", back_populates="procedures")

    # Indexes for performance
    __table_args__ = (
        Index("idx_procedure_drg", "ms_drg_code"),
        Index("idx_procedure_provider", "provider_id"),
        Index("idx_procedure_charges", "average_covered_charges"),
        Index("idx_procedure_payments", "average_total_payments"),
    )

    def __repr__(self) -> str:
        return f"<Procedure(drg='{self.ms_drg_code}', provider='{self.provider_id}')>"

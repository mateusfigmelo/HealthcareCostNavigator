"""Hospital model for storing provider information."""

from sqlalchemy import Column, Index, String
from sqlalchemy.orm import relationship

from .base import Base


class Hospital(Base):
    """Hospital/Provider model."""

    __tablename__ = "hospitals"

    provider_id = Column(String(20), primary_key=True, index=True)
    provider_name = Column(String(255), nullable=False)
    provider_city = Column(String(100), nullable=False)
    provider_state = Column(String(2), nullable=False)
    provider_zip_code = Column(String(10), nullable=False)

    # Relationships
    procedures = relationship("Procedure", back_populates="hospital")
    ratings = relationship("Rating", back_populates="hospital")

    # Indexes for performance
    __table_args__ = (
        Index("idx_hospital_zip", "provider_zip_code"),
        Index("idx_hospital_state", "provider_state"),
        Index("idx_hospital_city", "provider_city"),
    )

    def __repr__(self) -> str:
        return (
            f"<Hospital(provider_id='{self.provider_id}', name='{self.provider_name}')>"
        )

"""Rating model for storing hospital star ratings."""

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Rating(Base):
    """Hospital Rating model."""

    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(
        String(20), ForeignKey("hospitals.provider_id"), nullable=False
    )
    rating = Column(Float, nullable=False)  # 1-10 scale

    # Relationships
    hospital = relationship("Hospital", back_populates="ratings")

    # Indexes for performance
    __table_args__ = (
        Index("idx_rating_provider", "provider_id"),
        Index("idx_rating_value", "rating"),
    )

    def __repr__(self) -> str:
        return f"<Rating(provider='{self.provider_id}', rating={self.rating})>"

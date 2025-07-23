"""Provider service for hospital search and filtering."""

import math
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hospital, Procedure, Rating


class ProviderService:
    """Service for provider/hospital operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate haversine distance between two points in kilometers."""
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _zip_to_coordinates(self, zip_code: str) -> tuple[float, float] | None:
        """Convert ZIP code to coordinates (simplified - in production use a proper geocoding service)."""
        # This is a simplified mapping for NY ZIP codes
        # In production, you'd use a geocoding service like Google Maps API
        ny_zip_coords = {
            "10001": (40.7505, -73.9934),  # Manhattan
            "10010": (40.7387, -73.9864),  # Manhattan
            "10032": (40.8417, -73.9397),  # Manhattan
            "11211": (40.7128, -73.9564),  # Brooklyn
            "11201": (40.6943, -73.9866),  # Brooklyn
            "10011": (40.7415, -73.9982),  # Manhattan
            "10012": (40.7265, -73.9982),  # Manhattan
            "10013": (40.7205, -74.0082),  # Manhattan
            "10014": (40.7345, -74.0072),  # Manhattan
            "10016": (40.7455, -73.9782),  # Manhattan
        }

        return ny_zip_coords.get(zip_code)

    async def search_providers(
        self,
        drg: int | None = None,
        zip_code: str | None = None,
        radius_km: int | None = None,
        sort_by: str = "cost",
    ) -> list[dict[str, Any]]:
        """Search for providers by DRG, ZIP code, and radius."""

        # Build base query
        query = (
            select(Hospital, Procedure, func.avg(Rating.rating).label("avg_rating"))
            .outerjoin(Procedure, Hospital.provider_id == Procedure.provider_id)
            .outerjoin(Rating, Hospital.provider_id == Rating.provider_id)
        )

        # Apply filters
        conditions = []

        if drg:
            conditions.append(Procedure.ms_drg_code == str(drg))

        if zip_code and radius_km:
            # For now, we'll filter by ZIP code prefix (simplified approach)
            # In production, you'd use proper geospatial queries
            zip_prefix = zip_code[:3]  # First 3 digits for rough filtering
            conditions.append(Hospital.provider_zip_code.like(f"{zip_prefix}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Group by hospital and procedure
        query = query.group_by(
            Hospital.provider_id,
            Hospital.provider_name,
            Hospital.provider_city,
            Hospital.provider_state,
            Hospital.provider_zip_code,
            Procedure.id,
            Procedure.ms_drg_code,
            Procedure.ms_drg_definition,
            Procedure.total_discharges,
            Procedure.average_covered_charges,
            Procedure.average_total_payments,
            Procedure.average_medicare_payments,
        )

        # Apply sorting
        if sort_by == "cost":
            query = query.order_by(Procedure.average_covered_charges.asc())
        elif sort_by == "rating":
            query = query.order_by(func.avg(Rating.rating).desc())
        else:
            query = query.order_by(Procedure.average_covered_charges.asc())

        # Execute query
        try:
            result = await self.session.execute(query)
            rows = result.fetchall()
        except Exception as e:
            await self.session.rollback()
            raise e

        # Process results
        providers = []
        for row in rows:
            hospital, procedure, avg_rating = row

            if not hospital or not procedure:
                continue

            provider_data = {
                "provider_id": hospital.provider_id,
                "provider_name": hospital.provider_name,
                "provider_city": hospital.provider_city,
                "provider_state": hospital.provider_state,
                "provider_zip_code": hospital.provider_zip_code,
                "ms_drg_code": procedure.ms_drg_code,
                "ms_drg_definition": procedure.ms_drg_definition,
                "total_discharges": procedure.total_discharges,
                "average_covered_charges": procedure.average_covered_charges,
                "average_total_payments": procedure.average_total_payments,
                "average_medicare_payments": procedure.average_medicare_payments,
                "average_rating": round(avg_rating, 1) if avg_rating else None,
            }
            providers.append(provider_data)

        return providers

    async def search_by_text(
        self,
        search_text: str,
        zip_code: str | None = None,
        radius_km: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search providers by text description (fuzzy search)."""

        query = (
            select(Hospital, Procedure, func.avg(Rating.rating).label("avg_rating"))
            .outerjoin(Procedure, Hospital.provider_id == Procedure.provider_id)
            .outerjoin(Rating, Hospital.provider_id == Rating.provider_id)
        )

        # Text search conditions
        text_conditions = [
            Procedure.ms_drg_definition.ilike(f"%{search_text}%"),
            Hospital.provider_name.ilike(f"%{search_text}%"),
        ]

        conditions = [or_(*text_conditions)]

        if zip_code and radius_km:
            zip_prefix = zip_code[:3]
            conditions.append(Hospital.provider_zip_code.like(f"{zip_prefix}%"))

        query = query.where(and_(*conditions))
        query = query.group_by(
            Hospital.provider_id,
            Hospital.provider_name,
            Hospital.provider_city,
            Hospital.provider_state,
            Hospital.provider_zip_code,
            Procedure.id,
            Procedure.ms_drg_code,
            Procedure.ms_drg_definition,
            Procedure.total_discharges,
            Procedure.average_covered_charges,
            Procedure.average_total_payments,
            Procedure.average_medicare_payments,
        )
        query = query.order_by(Procedure.average_covered_charges.asc())

        try:
            result = await self.session.execute(query)
            rows = result.fetchall()
        except Exception as e:
            await self.session.rollback()
            raise e

        providers = []
        for row in rows:
            hospital, procedure, avg_rating = row

            if not hospital or not procedure:
                continue

            provider_data = {
                "provider_id": hospital.provider_id,
                "provider_name": hospital.provider_name,
                "provider_city": hospital.provider_city,
                "provider_state": hospital.provider_state,
                "provider_zip_code": hospital.provider_zip_code,
                "ms_drg_code": procedure.ms_drg_code,
                "ms_drg_definition": procedure.ms_drg_definition,
                "total_discharges": procedure.total_discharges,
                "average_covered_charges": procedure.average_covered_charges,
                "average_total_payments": procedure.average_total_payments,
                "average_medicare_payments": procedure.average_medicare_payments,
                "average_rating": round(avg_rating, 1) if avg_rating else None,
            }
            providers.append(provider_data)

        return providers

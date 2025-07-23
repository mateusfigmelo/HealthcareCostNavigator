"""Providers API router."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/", response_model=list[dict[str, Any]])
async def search_providers(
    drg: int | None = Query(None, description="MS-DRG code (e.g., 470)"),
    zip_code: str | None = Query(None, description="ZIP code for location search"),
    radius_km: int | None = Query(None, description="Search radius in kilometers"),
    sort_by: str = Query("cost", description="Sort by 'cost' or 'rating'"),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """
    Search for hospitals offering MS-DRG procedures.

    Returns hospitals sorted by average covered charges or ratings.
    Supports filtering by DRG code, ZIP code, and radius.
    """

    if sort_by not in ["cost", "rating"]:
        raise HTTPException(
            status_code=400, detail="sort_by must be 'cost' or 'rating'"
        )

    if radius_km and not zip_code:
        raise HTTPException(status_code=400, detail="radius_km requires zip_code")

    if radius_km and radius_km <= 0:
        raise HTTPException(status_code=400, detail="radius_km must be positive")

    provider_service = ProviderService(session)

    try:
        providers = await provider_service.search_providers(
            drg=drg, zip_code=zip_code, radius_km=radius_km, sort_by=sort_by
        )

        return providers

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.get("/search", response_model=list[dict[str, Any]])
async def search_by_text(
    q: str = Query(..., description="Search text for procedure or hospital name"),
    zip_code: str | None = Query(None, description="ZIP code for location search"),
    radius_km: int | None = Query(None, description="Search radius in kilometers"),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """
    Search for hospitals by text description.

    Supports fuzzy search on procedure definitions and hospital names.
    """

    if radius_km and not zip_code:
        raise HTTPException(status_code=400, detail="radius_km requires zip_code")

    if radius_km and radius_km <= 0:
        raise HTTPException(status_code=400, detail="radius_km must be positive")

    provider_service = ProviderService(session)

    try:
        providers = await provider_service.search_by_text(
            search_text=q, zip_code=zip_code, radius_km=radius_km
        )

        return providers

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e

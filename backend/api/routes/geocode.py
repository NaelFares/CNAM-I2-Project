"""Geocoding endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.services.geocoding import geocoding_service
from backend.api.schemas import GeocodeResult

router = APIRouter(prefix="/geocode", tags=["geocode"])


@router.get("/search", response_model=list[GeocodeResult])
def search_address(q: str = Query(min_length=3), limit: int = Query(default=5, ge=1, le=10)):
    return [GeocodeResult(**item) for item in geocoding_service.search_address(q, limit=limit)]


@router.get("/reverse", response_model=GeocodeResult | None)
def reverse_geocode(lat: float, lon: float):
    result = geocoding_service.reverse_geocode_details(lat=lat, lon=lon)
    if not result:
        return None
    return GeocodeResult(**result)

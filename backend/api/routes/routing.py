"""Route preview endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.services.routing import routing_service

from backend.api.deps import require_current_user

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/preview")
def preview_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    _user=Depends(require_current_user),
):
    details = routing_service.get_route_details((start_lat, start_lon), (end_lat, end_lon))
    if not details:
        return {"geometry": [], "distance_m": 0.0, "duration_s": 0.0}
    return {
        "geometry": [list(point) for point in details["geometry"]],
        "distance_m": details["distance_m"],
        "duration_s": details["duration_s"],
    }

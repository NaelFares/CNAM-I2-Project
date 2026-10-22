"""Aperçu de l’itinéraire sur la carte."""

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
    # Toujours un resultat : itineraire OSRM, ou estimation si OSRM est
    # indisponible (estimated=True, a signaler sous la carte).
    details = routing_service.get_route_details((start_lat, start_lon), (end_lat, end_lon))
    return {
        "geometry": [list(point) for point in details["geometry"]],
        "distance_m": details["distance_m"],
        "duration_s": details["duration_s"],
        "estimated": details["estimated"],
    }

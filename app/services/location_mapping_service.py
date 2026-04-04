from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class RouteEstimate:
    status: str
    distance_km: float
    eta_minutes: float


class LocationMappingService:
    """Simple route/ETA estimator that supports degraded GPS mode."""

    AVERAGE_CITY_SPEED_KMH = 28.0

    @classmethod
    def estimate_route(
        cls,
        *,
        pickup_lat: float | None,
        pickup_lng: float | None,
        dropoff_lat: float,
        dropoff_lng: float,
    ) -> RouteEstimate:
        if pickup_lat is None or pickup_lng is None:
            return RouteEstimate(status="degraded", distance_km=0.0, eta_minutes=0.0)

        distance_km = cls._haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        eta_minutes = (distance_km / cls.AVERAGE_CITY_SPEED_KMH) * 60.0 if distance_km > 0 else 0.0
        return RouteEstimate(status="ok", distance_km=round(distance_km, 3), eta_minutes=round(eta_minutes, 1))

    @staticmethod
    def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lng = radians(lng2 - lng1)
        a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
        return 2 * radius_km * asin(sqrt(a))

"""Distance calculation via the OSRM public demo API (actual road distances)."""

import httpx

from app.models import Location

OSRM_BASE = "https://router.project-osrm.org"


class RouteResult:
    def __init__(self, distance_km: float, duration_minutes: float):
        self.distance_km = distance_km
        self.duration_minutes = duration_minutes


async def get_driving_distance(origin: Location, destination: Location) -> RouteResult:
    """Return the driving distance (km) and duration (min) between two points.

    Uses the OSRM demo server which expects coordinates as longitude,latitude.
    """
    url = (
        f"{OSRM_BASE}/route/v1/driving/"
        f"{origin.longitude},{origin.latitude};"
        f"{destination.longitude},{destination.latitude}"
    )
    params = {"overview": "false"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM returned no route: {data.get('code', 'unknown')}")

    route = data["routes"][0]
    return RouteResult(
        distance_km=round(route["distance"] / 1000, 2),
        duration_minutes=round(route["duration"] / 60, 2),
    )


async def find_nearest_hospital_id(
    origin: Location,
    hospital_map: dict,
) -> tuple[str, RouteResult]:
    """Return (hospital_id, RouteResult) for the closest hospital by road."""
    if not hospital_map:
        raise ValueError("No hospitals registered")

    best_id: str | None = None
    best_route: RouteResult | None = None

    for h_id, hospital in hospital_map.items():
        route = await get_driving_distance(origin, hospital.location)
        if best_route is None or route.distance_km < best_route.distance_km:
            best_id = h_id
            best_route = route

    assert best_id is not None and best_route is not None
    return best_id, best_route

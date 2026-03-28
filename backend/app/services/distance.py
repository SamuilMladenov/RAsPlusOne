"""Distance calculation via the OSRM public demo API (actual road distances)."""

import httpx
import polyline as polyline_codec

from app.models import Location

OSRM_BASE = "https://router.project-osrm.org"


class RouteResult:
    def __init__(
        self,
        distance_km: float,
        duration_minutes: float,
        waypoints: list[Location] | None = None,
    ):
        self.distance_km = distance_km
        self.duration_minutes = duration_minutes
        self.waypoints = waypoints or []


async def get_driving_route(
    origin: Location,
    destination: Location,
    *,
    include_geometry: bool = False,
) -> RouteResult:
    """Return driving distance (km), duration (min), and optionally waypoints."""
    url = (
        f"{OSRM_BASE}/route/v1/driving/"
        f"{origin.longitude},{origin.latitude};"
        f"{destination.longitude},{destination.latitude}"
    )
    overview = "full" if include_geometry else "false"
    params = {"overview": overview, "geometries": "polyline"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM returned no route: {data.get('code', 'unknown')}")

    route = data["routes"][0]

    waypoints: list[Location] = []
    if include_geometry and route.get("geometry"):
        decoded = polyline_codec.decode(route["geometry"])
        waypoints = [Location(latitude=lat, longitude=lng) for lat, lng in decoded]

    return RouteResult(
        distance_km=round(route["distance"] / 1000, 2),
        duration_minutes=round(route["duration"] / 60, 2),
        waypoints=waypoints,
    )


async def get_driving_distance(origin: Location, destination: Location) -> RouteResult:
    """Convenience wrapper without geometry."""
    return await get_driving_route(origin, destination, include_geometry=False)


async def find_nearest_hospital_id(
    origin: Location,
    hospital_map: dict,
    *,
    include_geometry: bool = False,
) -> tuple[str, RouteResult]:
    """Return (hospital_id, RouteResult) for the closest hospital by road."""
    if not hospital_map:
        raise ValueError("No hospitals registered")

    best_id: str | None = None
    best_route: RouteResult | None = None

    for h_id, hospital in hospital_map.items():
        if hospital.available_beds <= 0:
            continue
        route = await get_driving_route(
            origin, hospital.location, include_geometry=include_geometry
        )
        if best_route is None or route.distance_km < best_route.distance_km:
            best_id = h_id
            best_route = route

    if best_id is None or best_route is None:
        raise ValueError("No hospitals with available beds")

    return best_id, best_route

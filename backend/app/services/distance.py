"""Distance calculation via the OSRM public demo API (actual road distances)."""

import math

import httpx
import polyline as polyline_codec

from app.models import Destination, Location

from app.services.hospital_beds import hospital_can_fulfill, hospital_total_available

OSRM_BASE = "https://router.project-osrm.org"

# Match simulation travel speed when OSRM is unavailable (straight-line fallback).
DEFAULT_SPEED_KMH = 60.0


def haversine_km(a: Location, b: Location) -> float:
    R = 6371.0
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


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


def straight_line_route(
    origin: Location,
    destination: Location,
    *,
    include_geometry: bool,
) -> RouteResult:
    """Approximate road route using great-circle distance and fixed speed."""
    km = round(haversine_km(origin, destination), 2)
    duration_minutes = round((km / DEFAULT_SPEED_KMH) * 60, 2)
    waypoints: list[Location] = [origin, destination] if include_geometry else []
    return RouteResult(
        distance_km=km,
        duration_minutes=duration_minutes,
        waypoints=waypoints,
    )


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

    # Simulation needs at least two points; OSRM can return empty geometry in edge cases.
    if include_geometry and len(waypoints) < 2:
        return straight_line_route(origin, destination, include_geometry=True)

    return RouteResult(
        distance_km=round(route["distance"] / 1000, 2),
        duration_minutes=round(route["duration"] / 60, 2),
        waypoints=waypoints,
    )


async def get_driving_route_with_fallback(
    origin: Location,
    destination: Location,
    *,
    include_geometry: bool = False,
) -> RouteResult:
    """OSRM route, or straight-line fallback if the service errors or rate-limits."""
    try:
        return await get_driving_route(origin, destination, include_geometry=include_geometry)
    except Exception:
        return straight_line_route(origin, destination, include_geometry=include_geometry)


async def get_driving_distance(origin: Location, destination: Location) -> RouteResult:
    """Convenience wrapper without geometry."""
    return await get_driving_route(origin, destination, include_geometry=False)


async def find_hospitals_sorted(
    origin: Location,
    hospital_map: dict,
    *,
    include_geometry: bool = False,
    bed_needs: dict[Destination, int] | None = None,
) -> list[tuple[str, RouteResult]]:
    """Return hospitals that can satisfy bed needs (or any free bed if needs is None),
    sorted by road distance from origin (nearest first).
    """
    if not hospital_map:
        raise ValueError("No hospitals registered")

    results: list[tuple[str, RouteResult]] = []
    for h_id, hospital in hospital_map.items():
        if bed_needs is not None:
            if not hospital_can_fulfill(hospital, bed_needs):
                continue
        elif hospital_total_available(hospital) <= 0:
            continue
        route = await get_driving_route_with_fallback(
            origin, hospital.location, include_geometry=include_geometry
        )
        results.append((h_id, route))

    results.sort(key=lambda x: x[1].distance_km)
    return results


async def find_nearest_hospital_id(
    origin: Location,
    hospital_map: dict,
    *,
    include_geometry: bool = False,
) -> tuple[str, RouteResult]:
    """Return (hospital_id, RouteResult) for the closest hospital by road."""
    results = await find_hospitals_sorted(
        origin, hospital_map, include_geometry=include_geometry
    )
    if not results:
        raise ValueError("No hospitals with available beds")
    return results[0]

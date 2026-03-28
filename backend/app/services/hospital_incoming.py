"""Build incoming-ambulance dashboard rows with OSRM-based ETA."""

from __future__ import annotations

import asyncio
import time

from app import database as db
from app.models import Ambulance, AmbulanceStatus, Hospital, Location
from app.schemas import IncomingAmbulanceLeg
from app.services.distance import DEFAULT_SPEED_KMH, get_driving_route, haversine_km

INCOMING_STATUSES = frozenset(
    {
        AmbulanceStatus.EN_ROUTE,
        AmbulanceStatus.AT_SCENE,
        AmbulanceStatus.TRANSPORTING,
    }
)

# OSRM calls are cached per ambulance+hospital+leg to avoid rate limits; TTL aligns with UI refresh.
ETA_CACHE_TTL_SECONDS = 60.0
# value: (expires_at_monotonic, eta_min, dist_km, err, approximate)
_eta_cache: dict[str, tuple[float, float | None, float | None, str | None, bool]] = {}


def prune_eta_cache() -> None:
    now = time.monotonic()
    stale = [k for k, (exp, *_rest) in _eta_cache.items() if now >= exp]
    for k in stale:
        del _eta_cache[k]


def _cache_key(ambulance: Ambulance, hospital: Hospital, leg: IncomingAmbulanceLeg) -> str:
    return f"{ambulance.ambulance_id}:{hospital.hospital_id}:{leg.value}"


def _straight_line_eta_minutes(a: Location, b: Location) -> tuple[float, float]:
    """Approximate driving time using haversine distance and simulation speed."""
    km = haversine_km(a, b)
    minutes = round((km / DEFAULT_SPEED_KMH) * 60, 2)
    return minutes, round(km, 2)


def leg_for_status(status: AmbulanceStatus) -> IncomingAmbulanceLeg:
    if status == AmbulanceStatus.EN_ROUTE:
        return IncomingAmbulanceLeg.TO_PATIENT
    if status == AmbulanceStatus.AT_SCENE:
        return IncomingAmbulanceLeg.AT_SCENE
    return IncomingAmbulanceLeg.TO_HOSPITAL


def _pickup_location(ambulance: Ambulance) -> tuple[Location | None, str | None]:
    for pid in ambulance.patient_ids:
        patient = db.patients.get(pid)
        if patient and patient.location:
            return patient.location, None
    return None, "No patient location"


async def _eta_to_hospital(
    ambulance: Ambulance, hospital: Hospital
) -> tuple[float | None, float | None, str | None, bool]:
    try:
        route = await get_driving_route(ambulance.location, hospital.location, include_geometry=False)
        return route.duration_minutes, route.distance_km, None, False
    except Exception:
        m, km = _straight_line_eta_minutes(ambulance.location, hospital.location)
        return m, km, None, True


async def compute_eta_minutes(
    ambulance: Ambulance,
    hospital: Hospital,
    leg: IncomingAmbulanceLeg,
) -> tuple[float | None, float | None, str | None, bool]:
    if leg in (IncomingAmbulanceLeg.TO_HOSPITAL, IncomingAmbulanceLeg.AT_SCENE):
        return await _eta_to_hospital(ambulance, hospital)

    pickup, reason = _pickup_location(ambulance)
    if pickup is None:
        return None, None, reason, False

    try:
        leg1, leg2 = await asyncio.gather(
            get_driving_route(ambulance.location, pickup, include_geometry=False),
            get_driving_route(pickup, hospital.location, include_geometry=False),
        )
        return (
            round(leg1.duration_minutes + leg2.duration_minutes, 2),
            round(leg1.distance_km + leg2.distance_km, 2),
            None,
            False,
        )
    except Exception:
        m1, km1 = _straight_line_eta_minutes(ambulance.location, pickup)
        m2, km2 = _straight_line_eta_minutes(pickup, hospital.location)
        return round(m1 + m2, 2), round(km1 + km2, 2), None, True


async def compute_eta_minutes_cached(
    ambulance: Ambulance,
    hospital: Hospital,
    leg: IncomingAmbulanceLeg,
) -> tuple[float | None, float | None, str | None, bool]:
    prune_eta_cache()
    key = _cache_key(ambulance, hospital, leg)
    now = time.monotonic()
    if key in _eta_cache:
        expires, eta, dist, err, approx = _eta_cache[key]
        if now < expires:
            return eta, dist, err, approx

    eta, dist, err, approx = await compute_eta_minutes(ambulance, hospital, leg)
    _eta_cache[key] = (now + ETA_CACHE_TTL_SECONDS, eta, dist, err, approx)
    return eta, dist, err, approx


async def incoming_row_dict(ambulance: Ambulance, hospital: Hospital) -> dict:
    leg = leg_for_status(ambulance.status)
    patients = []
    for pid in ambulance.patient_ids:
        p = db.patients.get(pid)
        if p:
            loc = p.location.model_dump() if p.location else None
            patients.append(
                {
                    "patient_id": p.patient_id,
                    "triage_status": p.triage_status,
                    "location": loc,
                }
            )

    eta_min, dist_km, eta_err, eta_approx = await compute_eta_minutes_cached(
        ambulance, hospital, leg
    )

    return {
        "ambulance_id": ambulance.ambulance_id,
        "status": ambulance.status,
        "leg": leg,
        "eta_minutes_to_hospital": eta_min,
        "distance_km_remaining": dist_km,
        "eta_approximate": eta_approx,
        "patients": patients,
        "eta_unavailable_reason": eta_err,
    }

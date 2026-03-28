"""Simulate ambulance travel along a route at a fixed speed."""

import asyncio
import math

from app.models import AmbulanceStatus, Location

SPEED_KMH = 60.0
TICK_SECONDS = 1.0

_active_tasks: dict[str, asyncio.Task] = {}


def _haversine_km(a: Location, b: Location) -> float:
    R = 6371.0
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _interpolate(a: Location, b: Location, fraction: float) -> Location:
    return Location(
        latitude=a.latitude + (b.latitude - a.latitude) * fraction,
        longitude=a.longitude + (b.longitude - a.longitude) * fraction,
    )


def _on_arrival(ambulance_id: str, ambulance):
    """Transfer patients from ambulance to hospital, then free the ambulance."""
    from app import database as db

    hospital = db.hospitals.get(ambulance.hospital_id) if ambulance.hospital_id else None

    for pid in ambulance.patient_ids:
        patient = db.patients.get(pid)
        if patient:
            patient.ambulance_id = None
            patient.location = None
        if hospital and pid not in hospital.patient_ids:
            hospital.patient_ids.append(pid)

    ambulance.patient_ids.clear()
    ambulance.hospital_id = None
    ambulance.status = AmbulanceStatus.AVAILABLE


async def _travel_leg(ambulance_id: str, ambulance, waypoints: list[Location]):
    """Move the ambulance along a single set of waypoints. Returns True if completed."""
    if len(waypoints) < 2:
        if waypoints:
            ambulance.location = waypoints[-1]
        return True

    seg_idx = 0
    seg_progress_km = 0.0
    seg_distance = _haversine_km(waypoints[0], waypoints[1])

    while seg_idx < len(waypoints) - 1:
        await asyncio.sleep(TICK_SECONDS)

        if ambulance_id not in _active_tasks:
            return False

        km_per_tick = SPEED_KMH * (TICK_SECONDS / 3600.0)
        seg_progress_km += km_per_tick

        while seg_progress_km >= seg_distance and seg_idx < len(waypoints) - 1:
            seg_progress_km -= seg_distance
            seg_idx += 1
            if seg_idx < len(waypoints) - 1:
                seg_distance = _haversine_km(waypoints[seg_idx], waypoints[seg_idx + 1])

        if seg_idx >= len(waypoints) - 1:
            ambulance.location = waypoints[-1]
            return True

        fraction = seg_progress_km / seg_distance if seg_distance > 0 else 0
        fraction = min(fraction, 1.0)
        ambulance.location = _interpolate(waypoints[seg_idx], waypoints[seg_idx + 1], fraction)

    return True


async def _run_two_leg_travel(
    ambulance_id: str,
    ambulance,
    pickup_waypoints: list[Location],
    hospital_waypoints: list[Location],
):
    """Leg 1: drive to patient (EN_ROUTE → AT_SCENE), Leg 2: drive to hospital (TRANSPORTING → unload)."""
    try:
        ambulance.status = AmbulanceStatus.EN_ROUTE

        if not await _travel_leg(ambulance_id, ambulance, pickup_waypoints):
            return

        ambulance.status = AmbulanceStatus.AT_SCENE
        await asyncio.sleep(2)
        if ambulance_id not in _active_tasks:
            return

        ambulance.status = AmbulanceStatus.TRANSPORTING

        if not await _travel_leg(ambulance_id, ambulance, hospital_waypoints):
            return

        _on_arrival(ambulance_id, ambulance)
    finally:
        _active_tasks.pop(ambulance_id, None)


async def _run_single_leg_travel(ambulance_id: str, ambulance, waypoints: list[Location]):
    """Single-leg travel directly to hospital (for assign-hospital without pickup)."""
    try:
        ambulance.status = AmbulanceStatus.TRANSPORTING

        if not await _travel_leg(ambulance_id, ambulance, waypoints):
            return

        _on_arrival(ambulance_id, ambulance)
    finally:
        _active_tasks.pop(ambulance_id, None)


def start_two_leg_travel(
    ambulance_id: str,
    ambulance,
    pickup_waypoints: list[Location],
    hospital_waypoints: list[Location],
):
    cancel_travel(ambulance_id)
    task = asyncio.create_task(
        _run_two_leg_travel(ambulance_id, ambulance, pickup_waypoints, hospital_waypoints)
    )
    _active_tasks[ambulance_id] = task


def start_travel(ambulance_id: str, ambulance, waypoints: list[Location]):
    cancel_travel(ambulance_id)
    task = asyncio.create_task(_run_single_leg_travel(ambulance_id, ambulance, waypoints))
    _active_tasks[ambulance_id] = task


def cancel_travel(ambulance_id: str):
    task = _active_tasks.pop(ambulance_id, None)
    if task and not task.done():
        task.cancel()

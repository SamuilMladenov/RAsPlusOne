"""Waiting-patient queue: triage-first dispatch, closest ambulance first, batching rules."""

from __future__ import annotations

from app import database as db
from app.models import AmbulanceStatus, Destination, Location, Patient, PatientStatus, TriagePriority
from app.services.distance import find_hospitals_sorted, get_driving_route_with_fallback
from app.services.hospital_beds import (
    count_bed_needs_from_patients,
    describe_bed_needs,
    hospital_can_fulfill,
    hospital_reserve,
)
from app.services.simulation import start_two_leg_travel

TRIAGE_SORT = {
    TriagePriority.RED: 0,
    TriagePriority.YELLOW: 1,
    TriagePriority.GREEN: 2,
    TriagePriority.BLACK: 99,
}


def effective_destination(p: Patient) -> Destination:
    return p.destination if p.destination is not None else Destination.GENERAL_HOSPITAL


def _location_key(p: Patient) -> tuple[float, float]:
    loc = p.location
    assert loc is not None
    return (round(loc.latitude, 5), round(loc.longitude, 5))


def sorted_waiting_patients(waiting: list[Patient]) -> list[Patient]:
    return sorted(
        waiting,
        key=lambda p: (TRIAGE_SORT.get(p.triage_priority, 99), p.patient_id),
    )


def select_next_batch(waiting_sorted: list[Patient]) -> list[str]:
    """Next load: one red, or one yellow, or up to two greens (same destination + pickup site)."""
    if not waiting_sorted:
        return []
    first = waiting_sorted[0]
    if first.triage_priority == TriagePriority.BLACK:
        return []
    if first.triage_priority == TriagePriority.RED:
        return [first.patient_id]
    if first.triage_priority == TriagePriority.YELLOW:
        return [first.patient_id]
    dest = effective_destination(first)
    lk = _location_key(first)
    for p in waiting_sorted[1:]:
        if (
            p.triage_priority == TriagePriority.GREEN
            and effective_destination(p) == dest
            and _location_key(p) == lk
        ):
            return [first.patient_id, p.patient_id]
    return [first.patient_id]


def emergency_batches_for_triage(triage: TriagePriority, pids: list[str]) -> list[list[str]]:
    """Red/yellow: one patient per ambulance. Green: pairs with same destination + location."""
    if triage in (TriagePriority.RED, TriagePriority.YELLOW):
        return [[pid] for pid in pids]
    groups: dict[tuple, list[str]] = {}
    for pid in pids:
        p = db.patients.get(pid)
        if not p or not p.location:
            continue
        key = (effective_destination(p), _location_key(p))
        groups.setdefault(key, []).append(pid)
    batches: list[list[str]] = []
    for ids in groups.values():
        ids.sort()
        for i in range(0, len(ids), 2):
            batches.append(ids[i : i + 2])
    return batches


async def try_dispatch_batch(
    patient_ids: list[str],
    *,
    pickup_location: Location | None = None,
) -> tuple[bool, dict | None]:
    """Pick closest available ambulance (by road to pickup), then best hospital leg.

    Returns (True, detail) with distance/duration if committed, else (False, None).
    """
    async with db.lock:
        patients: list[Patient] = []
        for pid in patient_ids:
            p = db.patients.get(pid)
            if not p or p.ambulance_id or p.status != PatientStatus.WAITING or not p.location:
                return False, None
            if p.triage_priority == TriagePriority.BLACK:
                return False, None
            patients.append(p)
        if not patients:
            return False, None
        loc = pickup_location or patients[0].location
        if loc is None:
            return False, None

    bed_needs = count_bed_needs_from_patients(patients)
    try:
        hospital_routes = await find_hospitals_sorted(
            loc, db.hospitals, include_geometry=True, bed_needs=bed_needs
        )
    except ValueError:
        return False, None

    if not hospital_routes:
        return False, None

    available = [a for a in db.ambulances.values() if a.status == AmbulanceStatus.AVAILABLE]
    if not available:
        return False, None

    # (pickup_km, hospital_km, amb, pickup_route, h_id, hospital_route)
    candidates: list[tuple] = []
    for amb in available:
        try:
            pickup_route = await get_driving_route_with_fallback(
                amb.location, loc, include_geometry=True
            )
        except Exception:
            continue
        for h_id, hospital_route in hospital_routes:
            candidates.append(
                (
                    pickup_route.distance_km,
                    hospital_route.distance_km,
                    amb,
                    pickup_route,
                    h_id,
                    hospital_route,
                )
            )

    candidates.sort(key=lambda c: (c[0], c[1]))

    if not candidates:
        return False, None

    async with db.lock:
        for pid in patient_ids:
            p = db.patients.get(pid)
            if not p or p.ambulance_id or p.status != PatientStatus.WAITING:
                return False, None

        for pickup_km, hospital_km, amb, pickup_route, h_id, hospital_route in candidates:
            if amb.status != AmbulanceStatus.AVAILABLE:
                continue
            hospital = db.hospitals.get(h_id)
            if not hospital or not hospital_can_fulfill(hospital, bed_needs):
                continue

            hospital_reserve(hospital, bed_needs)
            for pid in patient_ids:
                p = db.patients[pid]
                p.ambulance_id = amb.ambulance_id
                p.status = PatientStatus.IN_TRANSIT
                amb.patient_ids.append(pid)
            amb.hospital_id = h_id
            amb.status = AmbulanceStatus.EN_ROUTE

            start_two_leg_travel(
                amb.ambulance_id,
                amb,
                pickup_route.waypoints,
                hospital_route.waypoints,
            )
            total_km = pickup_km + hospital_km
            total_min = pickup_route.duration_minutes + hospital_route.duration_minutes
            return True, {
                "patient_ids": list(patient_ids),
                "ambulance_id": amb.ambulance_id,
                "hospital_id": h_id,
                "distance_km": round(total_km, 2),
                "duration_minutes": round(total_min, 2),
            }

    return False, None


async def process_waiting_dispatch_queue() -> None:
    """Assign waiting patients: red before yellow before green; closest ambulance first per batch."""
    while True:
        async with db.lock:
            waiting = [
                p
                for p in db.patients.values()
                if p.status == PatientStatus.WAITING
                and p.location
                and not p.ambulance_id
                and p.triage_priority != TriagePriority.BLACK
            ]
            batch = select_next_batch(sorted_waiting_patients(waiting))
        if not batch:
            break
        ok, _detail = await try_dispatch_batch(batch)
        if not ok and len(batch) == 2:
            ok, _detail = await try_dispatch_batch([batch[0]])
        if not ok:
            break


def describe_bed_needs_for_ids(patient_ids: list[str]) -> str:
    pts = [db.patients[pid] for pid in patient_ids if pid in db.patients]
    return describe_bed_needs(count_bed_needs_from_patients(pts))

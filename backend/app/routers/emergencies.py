import random
import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import (
    AmbulanceStatus,
    Patient,
    PatientStatus,
    TriagePriority,
    TRIAGE_AMBULANCE_CAPACITY,
)
from app.schemas import EmergencyCreate, EmergencyDispatch, EmergencyResponse
from app.services.distance import find_hospitals_sorted, get_driving_route_with_fallback
from app.services.simulation import start_two_leg_travel

router = APIRouter(prefix="/emergencies", tags=["Emergencies"])

TRIAGE_LEVELS = [TriagePriority.RED, TriagePriority.YELLOW, TriagePriority.GREEN]


@router.post("/", response_model=EmergencyResponse)
async def create_emergency(body: EmergencyCreate):
    """Create an emergency: bulk-create patients at a location with random triage,
    dispatch ambulances to pick them up, then route to nearest hospitals.

    All (ambulance, hospital) candidates are ranked. Under the lock each
    candidate is tried in order — stale ones are skipped instead of failing.
    """
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    # Create patients under lock
    patients_by_triage: dict[TriagePriority, list[str]] = {t: [] for t in TriagePriority}
    async with db.lock:
        for _ in range(body.patient_count):
            pid = f"EM-{uuid.uuid4().hex[:6].upper()}"
            triage = random.choice(TRIAGE_LEVELS)
            patient = Patient(patient_id=pid, triage_priority=triage, location=body.location)
            db.patients[pid] = patient
            patients_by_triage[triage].append(pid)

    # Pre-compute hospital routes from the emergency location (shared across batches)
    hospital_routes = await find_hospitals_sorted(
        body.location, db.hospitals, include_geometry=True
    )

    dispatched: list[EmergencyDispatch] = []
    unassigned: list[str] = []

    priority_order = [TriagePriority.RED, TriagePriority.YELLOW, TriagePriority.GREEN]

    for triage in priority_order:
        pids = patients_by_triage[triage]
        if not pids:
            continue
        capacity = TRIAGE_AMBULANCE_CAPACITY[triage]
        batches = [pids[i : i + capacity] for i in range(0, len(pids), capacity)]

        for batch in batches:
            available = [
                a for a in db.ambulances.values()
                if a.status == AmbulanceStatus.AVAILABLE
            ]
            if not available:
                unassigned.extend(batch)
                continue

            # Phase 1: compute pickup routes for all available ambulances (no lock)
            candidates: list[tuple] = []
            for amb in available:
                try:
                    pickup_route = await get_driving_route_with_fallback(
                        amb.location, body.location, include_geometry=True
                    )
                except Exception:
                    continue
                for h_id, hospital_route in hospital_routes:
                    total = pickup_route.distance_km + hospital_route.distance_km
                    candidates.append((total, amb, pickup_route, h_id, hospital_route))

            candidates.sort(key=lambda c: c[0])

            if not candidates:
                unassigned.extend(batch)
                continue

            # Phase 2: under lock, try candidates in order
            committed = False
            async with db.lock:
                for total_km, amb, pickup_route, h_id, hospital_route in candidates:
                    if amb.status != AmbulanceStatus.AVAILABLE:
                        continue
                    hospital = db.hospitals.get(h_id)
                    if not hospital or hospital.available_beds <= 0:
                        continue

                    hospital.available_beds -= 1

                    for pid in batch:
                        p = db.patients[pid]
                        p.ambulance_id = amb.ambulance_id
                        p.status = PatientStatus.IN_TRANSIT
                        amb.patient_ids.append(pid)

                    amb.hospital_id = h_id
                    amb.status = AmbulanceStatus.EN_ROUTE
                    committed = True

                    total_min = pickup_route.duration_minutes + hospital_route.duration_minutes

                    start_two_leg_travel(
                        amb.ambulance_id, amb,
                        pickup_route.waypoints, hospital_route.waypoints,
                    )

                    dispatched.append(EmergencyDispatch(
                        patient_ids=list(batch),
                        ambulance_id=amb.ambulance_id,
                        hospital_id=h_id,
                        distance_km=round(total_km, 2),
                        duration_minutes=round(total_min, 2),
                    ))
                    break

            if not committed:
                unassigned.extend(batch)

    return EmergencyResponse(dispatched=dispatched, unassigned_patients=unassigned)

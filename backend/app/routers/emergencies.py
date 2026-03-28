import random
import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import (
    AmbulanceStatus,
    Patient,
    TriageStatus,
    TRIAGE_AMBULANCE_CAPACITY,
)
from app.schemas import EmergencyCreate, EmergencyDispatch, EmergencyResponse
from app.services.distance import find_nearest_hospital_id, get_driving_route_with_fallback
from app.services.simulation import start_two_leg_travel

router = APIRouter(prefix="/emergencies", tags=["Emergencies"])

TRIAGE_LEVELS = list(TriageStatus)


@router.post("/", response_model=EmergencyResponse)
async def create_emergency(body: EmergencyCreate):
    """Create an emergency: bulk-create patients at a location with random triage,
    dispatch ambulances to pick them up, then route to nearest hospitals."""
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    patients_by_triage: dict[TriageStatus, list[str]] = {t: [] for t in TriageStatus}
    for _ in range(body.patient_count):
        pid = f"EM-{uuid.uuid4().hex[:6].upper()}"
        triage = random.choice(TRIAGE_LEVELS)
        patient = Patient(patient_id=pid, triage_status=triage, location=body.location)
        db.patients[pid] = patient
        patients_by_triage[triage].append(pid)

    dispatched: list[EmergencyDispatch] = []
    unassigned: list[str] = []

    priority_order = [TriageStatus.RED, TriageStatus.YELLOW, TriageStatus.GREEN]

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

            best_amb = None
            best_pickup_route = None
            best_hospital_route = None
            best_hospital_id = None

            for amb in available:
                try:
                    pickup_route = await get_driving_route_with_fallback(
                        amb.location, body.location, include_geometry=True
                    )
                    h_id, hospital_route = await find_nearest_hospital_id(
                        body.location, db.hospitals, include_geometry=True
                    )
                except Exception:
                    continue
                total = pickup_route.distance_km + hospital_route.distance_km
                best_total = (
                    (best_pickup_route.distance_km + best_hospital_route.distance_km)
                    if best_pickup_route and best_hospital_route
                    else float("inf")
                )
                if total < best_total:
                    best_amb = amb
                    best_pickup_route = pickup_route
                    best_hospital_route = hospital_route
                    best_hospital_id = h_id

            if (
                best_amb is None
                or best_pickup_route is None
                or best_hospital_route is None
                or best_hospital_id is None
            ):
                unassigned.extend(batch)
                continue

            hospital = db.hospitals.get(best_hospital_id)
            if hospital and hospital.available_beds <= 0:
                unassigned.extend(batch)
                continue
            if hospital:
                hospital.available_beds -= 1

            for pid in batch:
                patient = db.patients[pid]
                patient.ambulance_id = best_amb.ambulance_id
                best_amb.patient_ids.append(pid)

            best_amb.hospital_id = best_hospital_id
            best_amb.status = AmbulanceStatus.EN_ROUTE

            total_km = best_pickup_route.distance_km + best_hospital_route.distance_km
            total_min = best_pickup_route.duration_minutes + best_hospital_route.duration_minutes

            start_two_leg_travel(
                best_amb.ambulance_id,
                best_amb,
                best_pickup_route.waypoints,
                best_hospital_route.waypoints,
            )

            dispatched.append(EmergencyDispatch(
                patient_ids=list(batch),
                ambulance_id=best_amb.ambulance_id,
                hospital_id=best_hospital_id,
                distance_km=round(total_km, 2),
                duration_minutes=round(total_min, 2),
            ))

    return EmergencyResponse(dispatched=dispatched, unassigned_patients=unassigned)

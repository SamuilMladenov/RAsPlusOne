import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import AmbulanceStatus, Patient, PatientStatus
from app.schemas import (
    DispatchResponse,
    PatientCreate,
    PatientResponse,
)
from app.services.distance import find_hospitals_sorted, get_driving_route_with_fallback
from app.services.simulation import start_two_leg_travel

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(body: PatientCreate):
    patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
    patient = Patient(
        patient_id=patient_id,
        triage_priority=body.triage_priority,
        respiration=body.respiration,
        perfusion=body.perfusion,
        mental_status=body.mental_status,
        destination=body.destination,
        location=body.location,
    )
    async with db.lock:
        db.patients[patient_id] = patient
    return patient


@router.get("/", response_model=list[PatientResponse])
async def list_patients():
    return list(db.patients.values())


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(patient_id: str):
    async with db.lock:
        if patient_id not in db.patients:
            raise HTTPException(404, "Patient not found")
        patient = db.patients[patient_id]
        if patient.ambulance_id:
            amb = db.ambulances.get(patient.ambulance_id)
            if amb and patient_id in amb.patient_ids:
                amb.patient_ids.remove(patient_id)
        del db.patients[patient_id]


@router.post("/{patient_id}/dispatch", response_model=DispatchResponse)
async def dispatch_patient(patient_id: str):
    """Dispatch: find nearest ambulance, route it to the patient, then to the nearest hospital.

    All candidate (ambulance, hospital) pairs are ranked by total distance.
    Under the lock, candidates are tried in order — if one became stale
    (ambulance taken, hospital full), the next candidate is used instead of failing.
    """
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if patient.ambulance_id:
        raise HTTPException(409, "Patient is already assigned to an ambulance")
    if not patient.location:
        raise HTTPException(400, "Patient has no location set")
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    available = [
        a for a in db.ambulances.values()
        if a.status == AmbulanceStatus.AVAILABLE
    ]
    if not available:
        raise HTTPException(400, "No available ambulances")

    # Phase 1: compute routes for ALL ambulance+hospital combos (no lock)
    candidates: list[tuple] = []  # (total_km, amb, pickup_route, h_id, hospital_route)

    hospital_routes = await find_hospitals_sorted(
        patient.location, db.hospitals, include_geometry=True
    )
    if not hospital_routes:
        raise HTTPException(400, "No hospitals with available beds")

    for amb in available:
        try:
            pickup_route = await get_driving_route_with_fallback(
                amb.location, patient.location, include_geometry=True
            )
        except Exception:
            continue
        for h_id, hospital_route in hospital_routes:
            total_km = pickup_route.distance_km + hospital_route.distance_km
            candidates.append((total_km, amb, pickup_route, h_id, hospital_route))

    candidates.sort(key=lambda c: c[0])

    if not candidates:
        raise HTTPException(502, "Could not compute route for any ambulance")

    # Phase 2: under lock, try each candidate until one succeeds
    async with db.lock:
        if patient.ambulance_id:
            raise HTTPException(409, "Patient is already assigned to an ambulance")

        for total_km, amb, pickup_route, h_id, hospital_route in candidates:
            if amb.status != AmbulanceStatus.AVAILABLE:
                continue
            hospital = db.hospitals.get(h_id)
            if not hospital or hospital.available_beds <= 0:
                continue

            hospital.available_beds -= 1
            patient.ambulance_id = amb.ambulance_id
            patient.status = PatientStatus.IN_TRANSIT
            amb.patient_ids.append(patient_id)
            amb.hospital_id = h_id
            amb.status = AmbulanceStatus.EN_ROUTE

            total_min = pickup_route.duration_minutes + hospital_route.duration_minutes

            start_two_leg_travel(
                amb.ambulance_id, amb,
                pickup_route.waypoints, hospital_route.waypoints,
            )

            return DispatchResponse(
                patient_id=patient_id,
                ambulance_id=amb.ambulance_id,
                hospital_id=h_id,
                distance_km=round(total_km, 2),
                duration_minutes=round(total_min, 2),
            )

        raise HTTPException(
            400,
            "All ambulances or hospitals became unavailable during routing",
        )

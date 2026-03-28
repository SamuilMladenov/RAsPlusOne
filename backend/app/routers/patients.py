import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import AmbulanceStatus, Patient
from app.schemas import (
    DispatchResponse,
    PatientCreate,
    PatientResponse,
)
from app.services.distance import find_nearest_hospital_id, get_driving_route_with_fallback
from app.services.simulation import start_two_leg_travel

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(body: PatientCreate):
    patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
    patient = Patient(
        patient_id=patient_id,
        triage_status=body.triage_status,
        location=body.location,
    )
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
    """Dispatch: find nearest ambulance, route it to the patient, then to the nearest hospital."""
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

    best_amb = None
    best_pickup_route = None
    best_hospital_route = None
    best_hospital_id = None

    for amb in available:
        try:
            pickup_route = await get_driving_route_with_fallback(
                amb.location, patient.location, include_geometry=True
            )
            h_id, hospital_route = await find_nearest_hospital_id(
                patient.location, db.hospitals, include_geometry=True
            )
        except Exception:
            continue
        total_km = pickup_route.distance_km + hospital_route.distance_km
        best_total = (
            (best_pickup_route.distance_km + best_hospital_route.distance_km)
            if best_pickup_route and best_hospital_route
            else float("inf")
        )
        if total_km < best_total:
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
        raise HTTPException(502, "Could not compute route for any ambulance")

    hospital = db.hospitals.get(best_hospital_id)
    if hospital:
        if hospital.available_beds <= 0:
            raise HTTPException(400, f"Hospital '{best_hospital_id}' has no available beds")
        hospital.available_beds -= 1

    patient.ambulance_id = best_amb.ambulance_id
    best_amb.patient_ids.append(patient_id)
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

    return DispatchResponse(
        patient_id=patient_id,
        ambulance_id=best_amb.ambulance_id,
        hospital_id=best_hospital_id,
        distance_km=round(total_km, 2),
        duration_minutes=round(total_min, 2),
    )

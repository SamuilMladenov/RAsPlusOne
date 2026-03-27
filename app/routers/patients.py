from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import AmbulanceStatus, Patient
from app.schemas import (
    DispatchResponse,
    PatientCreate,
    PatientResponse,
)
from app.services.distance import find_nearest_hospital_id

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(body: PatientCreate):
    if body.patient_id in db.patients:
        raise HTTPException(409, f"Patient '{body.patient_id}' already exists")
    patient = Patient(patient_id=body.patient_id)
    db.patients[patient.patient_id] = patient
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
    """Full dispatch: assign the patient to the nearest available ambulance,
    then route that ambulance to the nearest hospital."""
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if patient.ambulance_id:
        raise HTTPException(409, "Patient is already assigned to an ambulance")
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    available = [
        a for a in db.ambulances.values()
        if a.status == AmbulanceStatus.AVAILABLE
    ]
    if not available:
        raise HTTPException(400, "No available ambulances")

    best_amb = None
    best_route = None
    best_hospital_id = None

    for amb in available:
        try:
            h_id, route = await find_nearest_hospital_id(
                amb.location, db.hospitals
            )
        except Exception:
            continue
        if best_route is None or route.distance_km < best_route.distance_km:
            best_amb = amb
            best_route = route
            best_hospital_id = h_id

    if best_amb is None or best_route is None or best_hospital_id is None:
        raise HTTPException(502, "Could not compute route for any ambulance")

    patient.ambulance_id = best_amb.ambulance_id
    best_amb.patient_ids.append(patient_id)
    best_amb.hospital_id = best_hospital_id
    best_amb.status = AmbulanceStatus.EN_ROUTE

    return DispatchResponse(
        patient_id=patient_id,
        ambulance_id=best_amb.ambulance_id,
        hospital_id=best_hospital_id,
        distance_km=best_route.distance_km,
        duration_minutes=best_route.duration_minutes,
    )

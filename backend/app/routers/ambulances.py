import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import Ambulance, AmbulanceStatus
from app.schemas import (
    AmbulanceCreate,
    AmbulanceResponse,
    AmbulanceUpdate,
    AssignHospitalResponse,
)
from app.services.distance import find_nearest_hospital_id
from app.services.simulation import cancel_travel, start_travel

router = APIRouter(prefix="/ambulances", tags=["Ambulances"])


def _reserve_bed(hospital_id: str):
    """Reserve one bed at the hospital for this ambulance assignment."""
    hospital = db.hospitals.get(hospital_id)
    if not hospital:
        return
    if hospital.available_beds <= 0:
        raise HTTPException(400, f"Hospital '{hospital_id}' has no available beds")
    hospital.available_beds -= 1


@router.post("/", response_model=AmbulanceResponse, status_code=201)
async def create_ambulance(body: AmbulanceCreate):
    ambulance_id = f"AMB-{uuid.uuid4().hex[:6].upper()}"
    ambulance = Ambulance(
        ambulance_id=ambulance_id,
        location=body.location,
    )
    db.ambulances[ambulance_id] = ambulance
    return ambulance


@router.get("/", response_model=list[AmbulanceResponse])
async def list_ambulances():
    return list(db.ambulances.values())


@router.get("/{ambulance_id}", response_model=AmbulanceResponse)
async def get_ambulance(ambulance_id: str):
    ambulance = db.ambulances.get(ambulance_id)
    if not ambulance:
        raise HTTPException(404, "Ambulance not found")
    return ambulance


@router.patch("/{ambulance_id}", response_model=AmbulanceResponse)
async def update_ambulance(ambulance_id: str, body: AmbulanceUpdate):
    ambulance = db.ambulances.get(ambulance_id)
    if not ambulance:
        raise HTTPException(404, "Ambulance not found")
    if body.location is not None:
        ambulance.location = body.location
    if body.status is not None:
        ambulance.status = body.status
    return ambulance


@router.delete("/{ambulance_id}", status_code=204)
async def delete_ambulance(ambulance_id: str):
    if ambulance_id not in db.ambulances:
        raise HTTPException(404, "Ambulance not found")
    cancel_travel(ambulance_id)
    del db.ambulances[ambulance_id]


@router.post(
    "/{ambulance_id}/assign-patient/{patient_id}",
    response_model=AmbulanceResponse,
)
async def assign_patient_to_ambulance(ambulance_id: str, patient_id: str):
    ambulance = db.ambulances.get(ambulance_id)
    if not ambulance:
        raise HTTPException(404, "Ambulance not found")
    patient = db.patients.get(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if patient.ambulance_id and patient.ambulance_id != ambulance_id:
        raise HTTPException(
            409,
            f"Patient already assigned to ambulance '{patient.ambulance_id}'",
        )

    if patient_id not in ambulance.patient_ids:
        ambulance.patient_ids.append(patient_id)
    patient.ambulance_id = ambulance_id

    if ambulance.status == AmbulanceStatus.AVAILABLE:
        ambulance.status = AmbulanceStatus.EN_ROUTE

    return ambulance


@router.post(
    "/{ambulance_id}/assign-hospital",
    response_model=AssignHospitalResponse,
)
async def assign_nearest_hospital(ambulance_id: str):
    """Find the nearest hospital by road distance, reserve beds, and start travel simulation."""
    ambulance = db.ambulances.get(ambulance_id)
    if not ambulance:
        raise HTTPException(404, "Ambulance not found")
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    try:
        hospital_id, route = await find_nearest_hospital_id(
            ambulance.location, db.hospitals, include_geometry=True
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Distance service error: {exc}") from exc

    _reserve_bed(hospital_id)
    ambulance.hospital_id = hospital_id
    ambulance.status = AmbulanceStatus.EN_ROUTE

    if route.waypoints:
        start_travel(ambulance_id, ambulance, route.waypoints)
    else:
        ambulance.status = AmbulanceStatus.AT_HOSPITAL

    return AssignHospitalResponse(
        ambulance_id=ambulance_id,
        hospital_id=hospital_id,
        distance_km=route.distance_km,
        duration_minutes=route.duration_minutes,
    )

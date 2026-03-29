import uuid

from fastapi import APIRouter, Depends, HTTPException

from app import database as db
from app.deps import require_admin
from app.models import Ambulance, AmbulanceStatus
from app.schemas import (
    AmbulanceCreate,
    AmbulanceResponse,
    AmbulanceUpdate,
    AssignHospitalResponse,
)
from app.services.distance import find_hospitals_sorted
from app.services.hospital_beds import (
    count_bed_needs_from_patients,
    hospital_can_fulfill,
    hospital_reserve,
)
from app.services.simulation import cancel_travel, start_travel

router = APIRouter(
    prefix="/ambulances",
    tags=["Ambulances"],
    dependencies=[Depends(require_admin)],
)


@router.post("/", response_model=AmbulanceResponse, status_code=201)
async def create_ambulance(body: AmbulanceCreate):
    ambulance_id = f"AMB-{uuid.uuid4().hex[:6].upper()}"
    ambulance = Ambulance(
        ambulance_id=ambulance_id,
        location=body.location,
    )
    async with db.lock:
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
    async with db.lock:
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
    async with db.lock:
        if ambulance_id not in db.ambulances:
            raise HTTPException(404, "Ambulance not found")
        cancel_travel(ambulance_id)
        del db.ambulances[ambulance_id]


@router.post(
    "/{ambulance_id}/assign-patient/{patient_id}",
    response_model=AmbulanceResponse,
)
async def assign_patient_to_ambulance(ambulance_id: str, patient_id: str):
    async with db.lock:
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
    """Find the nearest hospital by road distance, reserve beds, and start travel simulation.

    All hospitals are ranked by distance. Under the lock, each is tried in
    order — if one became full, the next nearest is used instead of failing.
    """
    ambulance = db.ambulances.get(ambulance_id)
    if not ambulance:
        raise HTTPException(404, "Ambulance not found")
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    patients_on_board = [
        db.patients[pid] for pid in ambulance.patient_ids if pid in db.patients
    ]
    if not patients_on_board:
        raise HTTPException(400, "Ambulance has no patients to transport")
    bed_needs = count_bed_needs_from_patients(patients_on_board)

    # Compute routes to all hospitals (outside lock)
    try:
        ranked = await find_hospitals_sorted(
            ambulance.location, db.hospitals, include_geometry=True, bed_needs=bed_needs
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Distance service error: {exc}") from exc

    if not ranked:
        raise HTTPException(400, "No hospitals with available beds")

    # Under lock, try each hospital in order
    async with db.lock:
        for hospital_id, route in ranked:
            hospital = db.hospitals.get(hospital_id)
            if not hospital or not hospital_can_fulfill(hospital, bed_needs):
                continue

            hospital_reserve(hospital, bed_needs)
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

        raise HTTPException(400, "All hospitals are full")

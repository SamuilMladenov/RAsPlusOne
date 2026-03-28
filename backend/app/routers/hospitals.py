import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import Hospital
from app.schemas import (
    HospitalCreate,
    HospitalDashboardResponse,
    HospitalResponse,
    HospitalUpdate,
    IncomingAmbulanceItem,
)
from app.services.hospital_incoming import INCOMING_STATUSES, incoming_row_dict

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.post("/", response_model=HospitalResponse, status_code=201)
async def create_hospital(body: HospitalCreate):
    hospital_id = f"H-{uuid.uuid4().hex[:6].upper()}"
    hospital = Hospital(
        hospital_id=hospital_id,
        location=body.location,
        doctors=body.doctors,
        burn_unit_beds_total=body.burn_unit_beds_total,
        burn_unit_beds_available=body.burn_unit_beds_available,
        trauma_center_beds_total=body.trauma_center_beds_total,
        trauma_center_beds_available=body.trauma_center_beds_available,
        general_beds_total=body.general_beds_total,
        general_beds_available=body.general_beds_available,
    )
    async with db.lock:
        db.hospitals[hospital_id] = hospital
    return hospital


@router.get("/", response_model=list[HospitalResponse])
async def list_hospitals():
    return list(db.hospitals.values())


@router.get("/{hospital_id}/dashboard", response_model=HospitalDashboardResponse)
async def get_hospital_dashboard(hospital_id: str):
    hospital = db.hospitals.get(hospital_id)
    if not hospital:
        raise HTTPException(404, "Hospital not found")

    incoming_ambs = [
        a
        for a in db.ambulances.values()
        if a.hospital_id == hospital_id and a.status in INCOMING_STATUSES
    ]
    row_dicts = await asyncio.gather(
        *[incoming_row_dict(a, hospital) for a in incoming_ambs]
    )
    incoming = [IncomingAmbulanceItem(**r) for r in row_dicts]
    incoming.sort(
        key=lambda x: (
            x.eta_minutes_to_hospital is None,
            x.eta_minutes_to_hospital if x.eta_minutes_to_hospital is not None else 0.0,
            x.ambulance_id,
        )
    )

    return HospitalDashboardResponse(
        hospital=HospitalResponse.model_validate(hospital.model_dump()),
        incoming=incoming,
    )


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str):
    hospital = db.hospitals.get(hospital_id)
    if not hospital:
        raise HTTPException(404, "Hospital not found")
    return hospital


@router.patch("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(hospital_id: str, body: HospitalUpdate):
    async with db.lock:
        hospital = db.hospitals.get(hospital_id)
        if not hospital:
            raise HTTPException(404, "Hospital not found")
        if body.location is not None:
            hospital.location = body.location
        if body.doctors is not None:
            hospital.doctors = body.doctors
        if body.burn_unit_beds_total is not None:
            hospital.burn_unit_beds_total = body.burn_unit_beds_total
        if body.burn_unit_beds_available is not None:
            hospital.burn_unit_beds_available = body.burn_unit_beds_available
        if body.trauma_center_beds_total is not None:
            hospital.trauma_center_beds_total = body.trauma_center_beds_total
        if body.trauma_center_beds_available is not None:
            hospital.trauma_center_beds_available = body.trauma_center_beds_available
        if body.general_beds_total is not None:
            hospital.general_beds_total = body.general_beds_total
        if body.general_beds_available is not None:
            hospital.general_beds_available = body.general_beds_available
        if hospital.burn_unit_beds_total < hospital.burn_unit_beds_available:
            hospital.burn_unit_beds_total = hospital.burn_unit_beds_available
        if hospital.trauma_center_beds_total < hospital.trauma_center_beds_available:
            hospital.trauma_center_beds_total = hospital.trauma_center_beds_available
        if hospital.general_beds_total < hospital.general_beds_available:
            hospital.general_beds_total = hospital.general_beds_available
    return hospital


@router.delete("/{hospital_id}", status_code=204)
async def delete_hospital(hospital_id: str):
    async with db.lock:
        if hospital_id not in db.hospitals:
            raise HTTPException(404, "Hospital not found")
        del db.hospitals[hospital_id]

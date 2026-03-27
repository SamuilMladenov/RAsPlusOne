from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import Hospital
from app.schemas import HospitalCreate, HospitalResponse, HospitalUpdate

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.post("/", response_model=HospitalResponse, status_code=201)
async def create_hospital(body: HospitalCreate):
    if body.hospital_id in db.hospitals:
        raise HTTPException(409, f"Hospital '{body.hospital_id}' already exists")
    hospital = Hospital(
        hospital_id=body.hospital_id,
        location=body.location,
        doctors=body.doctors,
    )
    db.hospitals[hospital.hospital_id] = hospital
    return hospital


@router.get("/", response_model=list[HospitalResponse])
async def list_hospitals():
    return list(db.hospitals.values())


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str):
    hospital = db.hospitals.get(hospital_id)
    if not hospital:
        raise HTTPException(404, "Hospital not found")
    return hospital


@router.patch("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(hospital_id: str, body: HospitalUpdate):
    hospital = db.hospitals.get(hospital_id)
    if not hospital:
        raise HTTPException(404, "Hospital not found")
    if body.location is not None:
        hospital.location = body.location
    if body.doctors is not None:
        hospital.doctors = body.doctors
    return hospital


@router.delete("/{hospital_id}", status_code=204)
async def delete_hospital(hospital_id: str):
    if hospital_id not in db.hospitals:
        raise HTTPException(404, "Hospital not found")
    del db.hospitals[hospital_id]

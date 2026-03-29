import uuid

from fastapi import APIRouter, Depends, HTTPException

from app import database as db
from app.deps import require_admin
from app.models import Patient, PatientStatus, TriagePriority
from app.schemas import (
    DispatchResponse,
    PatientCreate,
    PatientResponse,
)
from app.realtime import notify_patients_changed
from app.services.dispatch_queue import (
    describe_bed_needs_for_ids,
    process_waiting_dispatch_queue,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    dependencies=[Depends(require_admin)],
)


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
    await process_waiting_dispatch_queue()
    await notify_patients_changed()
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
    await notify_patients_changed()


@router.post("/{patient_id}/dispatch", response_model=DispatchResponse)
async def dispatch_patient(patient_id: str):
    """Run the global dispatch queue (triage order: red, then yellow, then green).

    The given patient is assigned only when it is their turn and resources exist.
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
    if patient.triage_priority == TriagePriority.BLACK:
        raise HTTPException(400, "Black-triage patients are not transported")

    await process_waiting_dispatch_queue()

    patient = db.patients.get(patient_id)
    if not patient or not patient.ambulance_id:
        bed_hint = describe_bed_needs_for_ids([patient_id])
        raise HTTPException(
            400,
            "Patient could not be assigned yet (higher-priority patients waiting, "
            "no free ambulance, or no hospital with matching beds: "
            + bed_hint
            + ")",
        )

    amb = db.ambulances.get(patient.ambulance_id)
    if not amb or not amb.hospital_id:
        raise HTTPException(500, "Inconsistent ambulance state after dispatch")

    await notify_patients_changed()
    return DispatchResponse(
        patient_id=patient_id,
        ambulance_id=patient.ambulance_id,
        hospital_id=amb.hospital_id,
        distance_km=0.0,
        duration_minutes=0.0,
    )

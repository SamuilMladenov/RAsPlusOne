import uuid

from fastapi import APIRouter, Depends, HTTPException

from app import database as db
from app.deps import require_admin
from app.models import AmbulanceStatus, Patient, TriagePriority
from app.schemas import EmergencyCreate, EmergencyDispatch, EmergencyResponse
from app.realtime import notify_patients_changed
from app.services.dispatch_queue import emergency_batches_for_triage, try_dispatch_batch

router = APIRouter(
    prefix="/emergencies",
    tags=["Emergencies"],
    dependencies=[Depends(require_admin)],
)


@router.post("/", response_model=EmergencyResponse)
async def create_emergency(body: EmergencyCreate):
    """Bulk-create patients at a scene; dispatch uses triage order and new capacity rules.

    Red/yellow: one patient per ambulance. Green: up to two per ambulance if they share
    destination and location. Closest available ambulance to the scene is chosen first.
    Clinical fields are supplied by the client (e.g. randomized in the UI).
    """
    if not db.hospitals:
        raise HTTPException(400, "No hospitals registered in the system")

    patients_by_triage: dict[TriagePriority, list[str]] = {t: [] for t in TriagePriority}
    async with db.lock:
        for spec in body.patients:
            pid = f"EM-{uuid.uuid4().hex[:6].upper()}"
            patient = Patient(
                patient_id=pid,
                triage_priority=spec.triage_priority,
                location=body.location,
                destination=spec.destination,
                respiration=spec.respiration,
                perfusion=spec.perfusion,
                mental_status=spec.mental_status,
            )
            db.patients[pid] = patient
            patients_by_triage[spec.triage_priority].append(pid)

    dispatched: list[EmergencyDispatch] = []
    unassigned: list[str] = []

    priority_order = [TriagePriority.RED, TriagePriority.YELLOW, TriagePriority.GREEN]

    for triage in priority_order:
        pids = patients_by_triage[triage]
        if not pids:
            continue
        batches = emergency_batches_for_triage(triage, pids)

        for batch in batches:
            available = [
                a for a in db.ambulances.values()
                if a.status == AmbulanceStatus.AVAILABLE
            ]
            if not available:
                unassigned.extend(batch)
                continue

            ok, detail = await try_dispatch_batch(batch, pickup_location=body.location)
            if not ok and len(batch) == 2:
                ok, detail = await try_dispatch_batch([batch[0]], pickup_location=body.location)
                if ok and detail:
                    unassigned.append(batch[1])
                    dispatched.append(
                        EmergencyDispatch(
                            patient_ids=detail["patient_ids"],
                            ambulance_id=detail["ambulance_id"],
                            hospital_id=detail["hospital_id"],
                            distance_km=detail["distance_km"],
                            duration_minutes=detail["duration_minutes"],
                        )
                    )
                else:
                    unassigned.extend(batch)
            elif ok and detail:
                dispatched.append(
                    EmergencyDispatch(
                        patient_ids=detail["patient_ids"],
                        ambulance_id=detail["ambulance_id"],
                        hospital_id=detail["hospital_id"],
                        distance_km=detail["distance_km"],
                        duration_minutes=detail["duration_minutes"],
                    )
                )
            else:
                unassigned.extend(batch)

    await notify_patients_changed()
    return EmergencyResponse(dispatched=dispatched, unassigned_patients=unassigned)

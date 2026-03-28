from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import AmbulanceStatus, Location, TriageStatus


# ── Patient ──────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    triage_status: TriageStatus = TriageStatus.GREEN


class PatientResponse(BaseModel):
    patient_id: str
    ambulance_id: Optional[str] = None
    triage_status: TriageStatus


# ── Ambulance ────────────────────────────────────────────────────────

class AmbulanceCreate(BaseModel):
    location: Location


class AmbulanceUpdate(BaseModel):
    location: Optional[Location] = None
    status: Optional[AmbulanceStatus] = None


class AmbulanceResponse(BaseModel):
    ambulance_id: str
    patient_ids: list[str]
    location: Location
    hospital_id: Optional[str] = None
    status: AmbulanceStatus


# ── Hospital ─────────────────────────────────────────────────────────

class HospitalCreate(BaseModel):
    location: Location
    doctors: list[str] = Field(default_factory=list)
    available_beds: int = Field(default=10, ge=0)


class HospitalUpdate(BaseModel):
    location: Optional[Location] = None
    doctors: Optional[list[str]] = None
    available_beds: Optional[int] = None


class HospitalResponse(BaseModel):
    hospital_id: str
    location: Location
    doctors: list[str]
    available_beds: int
    patient_ids: list[str]


# ── Assignment ───────────────────────────────────────────────────────

class AssignHospitalResponse(BaseModel):
    ambulance_id: str
    hospital_id: str
    distance_km: float
    duration_minutes: float


class DispatchResponse(BaseModel):
    patient_id: str
    ambulance_id: str
    hospital_id: str
    distance_km: float
    duration_minutes: float


# ── Emergency ────────────────────────────────────────────────────────

class EmergencyCreate(BaseModel):
    location: Location
    patient_count: int = Field(..., ge=1)


class EmergencyDispatch(BaseModel):
    patient_ids: list[str]
    ambulance_id: str
    hospital_id: str
    distance_km: float
    duration_minutes: float


class EmergencyResponse(BaseModel):
    dispatched: list[EmergencyDispatch]
    unassigned_patients: list[str]

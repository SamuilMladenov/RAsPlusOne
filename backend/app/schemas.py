from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import AmbulanceStatus, Location


# ── Patient ──────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    patient_id: str


class PatientResponse(BaseModel):
    patient_id: str
    ambulance_id: Optional[str] = None


# ── Ambulance ────────────────────────────────────────────────────────

class AmbulanceCreate(BaseModel):
    ambulance_id: str
    location: Location
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE


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
    hospital_id: str
    location: Location
    doctors: list[str] = Field(default_factory=list)


class HospitalUpdate(BaseModel):
    location: Optional[Location] = None
    doctors: Optional[list[str]] = None


class HospitalResponse(BaseModel):
    hospital_id: str
    location: Location
    doctors: list[str]


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

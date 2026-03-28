from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from enum import Enum

from app.models import (
    AmbulanceStatus,
    Destination,
    Location,
    MentalStatus,
    PatientStatus,
    Perfusion,
    Respiration,
    TriagePriority,
)


class IncomingAmbulanceLeg(str, Enum):
    TO_PATIENT = "to_patient"
    AT_SCENE = "at_scene"
    TO_HOSPITAL = "to_hospital"


# ── Patient ──────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    location: Location
    triage_priority: TriagePriority = TriagePriority.GREEN
    respiration: Optional[Respiration] = None
    perfusion: Optional[Perfusion] = None
    mental_status: Optional[MentalStatus] = None
    destination: Optional[Destination] = None


class PatientResponse(BaseModel):
    patient_id: str
    ambulance_id: Optional[str] = None
    triage_priority: TriagePriority
    respiration: Optional[Respiration] = None
    perfusion: Optional[Perfusion] = None
    mental_status: Optional[MentalStatus] = None
    destination: Optional[Destination] = None
    status: PatientStatus
    location: Optional[Location] = None


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
    total_beds: int = Field(default=10, ge=0)
    available_beds: int = Field(default=10, ge=0)

    @model_validator(mode="after")
    def total_covers_available(self) -> HospitalCreate:
        if self.total_beds < self.available_beds:
            self.total_beds = self.available_beds
        return self


class HospitalUpdate(BaseModel):
    location: Optional[Location] = None
    doctors: Optional[list[str]] = None
    total_beds: Optional[int] = None
    available_beds: Optional[int] = None


class HospitalResponse(BaseModel):
    hospital_id: str
    location: Location
    doctors: list[str]
    total_beds: int
    available_beds: int
    patient_ids: list[str]


# ── Hospital dashboard (incoming ambulances) ─────────────────────────

class IncomingPatientBrief(BaseModel):
    patient_id: str
    triage_priority: TriagePriority
    location: Optional[Location] = None


class IncomingAmbulanceItem(BaseModel):
    ambulance_id: str
    status: AmbulanceStatus
    leg: IncomingAmbulanceLeg
    eta_minutes_to_hospital: Optional[float] = None
    distance_km_remaining: Optional[float] = None
    eta_approximate: bool = False
    patients: list[IncomingPatientBrief]
    eta_unavailable_reason: Optional[str] = None


class HospitalDashboardResponse(BaseModel):
    hospital: HospitalResponse
    incoming: list[IncomingAmbulanceItem]


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

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

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

    @field_validator("respiration", "perfusion", "mental_status", "destination", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v


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
    burn_unit_beds_total: int = Field(default=4, ge=0)
    burn_unit_beds_available: int = Field(default=4, ge=0)
    trauma_center_beds_total: int = Field(default=4, ge=0)
    trauma_center_beds_available: int = Field(default=4, ge=0)
    general_beds_total: int = Field(default=4, ge=0)
    general_beds_available: int = Field(default=4, ge=0)

    @model_validator(mode="after")
    def totals_cover_available(self) -> HospitalCreate:
        if self.burn_unit_beds_total < self.burn_unit_beds_available:
            self.burn_unit_beds_total = self.burn_unit_beds_available
        if self.trauma_center_beds_total < self.trauma_center_beds_available:
            self.trauma_center_beds_total = self.trauma_center_beds_available
        if self.general_beds_total < self.general_beds_available:
            self.general_beds_total = self.general_beds_available
        return self


class HospitalUpdate(BaseModel):
    location: Optional[Location] = None
    doctors: Optional[list[str]] = None
    burn_unit_beds_total: Optional[int] = Field(default=None, ge=0)
    burn_unit_beds_available: Optional[int] = Field(default=None, ge=0)
    trauma_center_beds_total: Optional[int] = Field(default=None, ge=0)
    trauma_center_beds_available: Optional[int] = Field(default=None, ge=0)
    general_beds_total: Optional[int] = Field(default=None, ge=0)
    general_beds_available: Optional[int] = Field(default=None, ge=0)


class HospitalResponse(BaseModel):
    hospital_id: str
    location: Location
    doctors: list[str]
    burn_unit_beds_total: int
    burn_unit_beds_available: int
    trauma_center_beds_total: int
    trauma_center_beds_available: int
    general_beds_total: int
    general_beds_available: int
    patient_ids: list[str]


# ── Hospital dashboard (incoming ambulances) ─────────────────────────

class IncomingAmbulanceItem(BaseModel):
    ambulance_id: str
    status: AmbulanceStatus
    leg: IncomingAmbulanceLeg
    eta_minutes_to_hospital: Optional[float] = None
    distance_km_remaining: Optional[float] = None
    eta_approximate: bool = False
    patients: list[PatientResponse]
    eta_unavailable_reason: Optional[str] = None


class DepartmentDashboardItem(BaseModel):
    destination: Destination
    label: str
    beds_total: int
    beds_available: int
    patients: list[PatientResponse]


class HospitalDashboardResponse(BaseModel):
    hospital: HospitalResponse
    incoming: list[IncomingAmbulanceItem]
    departments: list[DepartmentDashboardItem]


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

class EmergencyPatientInput(BaseModel):
    triage_priority: TriagePriority
    destination: Destination
    respiration: Respiration
    perfusion: Perfusion
    mental_status: MentalStatus


class EmergencyCreate(BaseModel):
    location: Location
    patients: list[EmergencyPatientInput] = Field(..., min_length=1)


class EmergencyDispatch(BaseModel):
    patient_ids: list[str]
    ambulance_id: str
    hospital_id: str
    distance_km: float
    duration_minutes: float


class EmergencyResponse(BaseModel):
    dispatched: list[EmergencyDispatch]
    unassigned_patients: list[str]

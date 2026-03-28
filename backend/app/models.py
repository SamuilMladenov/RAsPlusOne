from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TriageStatus(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


TRIAGE_AMBULANCE_CAPACITY = {
    TriageStatus.RED: 1,
    TriageStatus.YELLOW: 3,
    TriageStatus.GREEN: 5,
}


class AmbulanceStatus(str, Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    AT_SCENE = "at_scene"
    TRANSPORTING = "transporting"
    AT_HOSPITAL = "at_hospital"
    OUT_OF_SERVICE = "out_of_service"


class Patient(BaseModel):
    patient_id: str
    ambulance_id: Optional[str] = None
    triage_status: TriageStatus = TriageStatus.GREEN


class Ambulance(BaseModel):
    ambulance_id: str
    patient_ids: list[str] = Field(default_factory=list)
    location: Location
    hospital_id: Optional[str] = None
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE


class Hospital(BaseModel):
    hospital_id: str
    location: Location
    doctors: list[str] = Field(default_factory=list)
    available_beds: int = Field(default=0, ge=0)
    patient_ids: list[str] = Field(default_factory=list)

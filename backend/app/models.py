from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TriagePriority(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLACK = "black"


TRIAGE_AMBULANCE_CAPACITY = {
    TriagePriority.RED: 1,
    TriagePriority.YELLOW: 3,
    TriagePriority.GREEN: 5,
    TriagePriority.BLACK: 0,
}


class Respiration(str, Enum):
    NOT_BREATHING = "Not Breathing"
    UNDER_10 = "< 10 / min"
    NORMAL = "10 - 30 / min"
    OVER_30 = "> 30 / min"


class Perfusion(str, Enum):
    RADIAL_PRESENT = "Radial pulse present"
    NO_RADIAL = "No radial pulse"
    CAP_UNDER_2 = "Capillary refill < 2 sec"
    CAP_OVER_2 = "Capillary refill > 2 sec"
    SEVERE_BLEEDING = "Severe bleeding"


class MentalStatus(str, Enum):
    ALERT = "Alert"
    UNRESPONSIVE = "Unresponsive"
    CANNOT_FOLLOW = "Cannot follow commands"


class Destination(str, Enum):
    TRAUMA_CENTER = "Trauma Center"
    GENERAL_HOSPITAL = "General Hospital"
    BURN_UNIT = "Burn Unit"


class AmbulanceStatus(str, Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    AT_SCENE = "at_scene"
    TRANSPORTING = "transporting"
    AT_HOSPITAL = "at_hospital"
    OUT_OF_SERVICE = "out_of_service"


class PatientStatus(str, Enum):
    WAITING = "waiting"
    IN_TRANSIT = "in_transit"
    ADMITTED = "admitted"


class Patient(BaseModel):
    patient_id: str
    ambulance_id: Optional[str] = None
    triage_priority: TriagePriority = TriagePriority.GREEN
    respiration: Optional[Respiration] = None
    perfusion: Optional[Perfusion] = None
    mental_status: Optional[MentalStatus] = None
    destination: Optional[Destination] = None
    status: PatientStatus = PatientStatus.WAITING
    location: Optional[Location] = None


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
    total_beds: int = Field(default=10, ge=0)
    available_beds: int = Field(default=0, ge=0)
    patient_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def total_beds_covers_available(self) -> Hospital:
        if self.total_beds < self.available_beds:
            self.total_beds = self.available_beds
        return self

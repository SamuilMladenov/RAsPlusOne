"""Aggregate department occupancy for the hospital dashboard."""

from __future__ import annotations

from app import database as db
from app.models import Destination, PatientStatus
from app.schemas import DepartmentDashboardItem, PatientResponse
from app.services.dispatch_queue import effective_destination

_DEPARTMENTS: tuple[tuple[Destination, str], ...] = (
    (Destination.BURN_UNIT, "Burn Unit"),
    (Destination.TRAUMA_CENTER, "Trauma Center"),
    (Destination.GENERAL_HOSPITAL, "General Hospital"),
)


def _bed_counts(hospital, dest: Destination) -> tuple[int, int]:
    if dest == Destination.BURN_UNIT:
        return hospital.burn_unit_beds_total, hospital.burn_unit_beds_available
    if dest == Destination.TRAUMA_CENTER:
        return hospital.trauma_center_beds_total, hospital.trauma_center_beds_available
    return hospital.general_beds_total, hospital.general_beds_available


def build_department_dashboard(hospital) -> list[DepartmentDashboardItem]:
    rows: list[DepartmentDashboardItem] = []
    for dest, label in _DEPARTMENTS:
        total, avail = _bed_counts(hospital, dest)
        pts: list[PatientResponse] = []
        for pid in hospital.patient_ids:
            p = db.patients.get(pid)
            if not p or p.status != PatientStatus.ADMITTED:
                continue
            if effective_destination(p) != dest:
                continue
            pts.append(PatientResponse.model_validate(p))
        pts.sort(key=lambda x: x.patient_id)
        rows.append(
            DepartmentDashboardItem(
                destination=dest,
                label=label,
                beds_total=total,
                beds_available=avail,
                patients=pts,
            )
        )
    return rows

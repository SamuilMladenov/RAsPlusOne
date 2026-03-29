"""Bed capacity by destination type (burn / trauma / general)."""

from __future__ import annotations

from collections import Counter

from app.models import Destination, Hospital


def count_bed_needs_from_patients(patients: list) -> dict[Destination, int]:
    """How many beds of each type are needed (unset destination → general)."""
    c: Counter[Destination] = Counter()
    for p in patients:
        d = p.destination if p.destination is not None else Destination.GENERAL_HOSPITAL
        c[d] += 1
    return dict(c)


def hospital_total_available(hospital: Hospital) -> int:
    return (
        hospital.burn_unit_beds_available
        + hospital.trauma_center_beds_available
        + hospital.general_beds_available
    )


def hospital_can_fulfill(hospital: Hospital, needs: dict[Destination, int]) -> bool:
    b = needs.get(Destination.BURN_UNIT, 0)
    t = needs.get(Destination.TRAUMA_CENTER, 0)
    g = needs.get(Destination.GENERAL_HOSPITAL, 0)
    return (
        hospital.burn_unit_beds_available >= b
        and hospital.trauma_center_beds_available >= t
        and hospital.general_beds_available >= g
    )


def hospital_reserve(hospital: Hospital, needs: dict[Destination, int]) -> None:
    hospital.burn_unit_beds_available -= needs.get(Destination.BURN_UNIT, 0)
    hospital.trauma_center_beds_available -= needs.get(Destination.TRAUMA_CENTER, 0)
    hospital.general_beds_available -= needs.get(Destination.GENERAL_HOSPITAL, 0)


_DEST_LABEL = {
    Destination.BURN_UNIT: "Burn Unit",
    Destination.TRAUMA_CENTER: "Trauma Center",
    Destination.GENERAL_HOSPITAL: "General Hospital",
}


def describe_bed_needs(needs: dict[Destination, int]) -> str:
    """Human-readable list of required bed slots (for error messages)."""
    parts: list[str] = []
    for dest in (Destination.BURN_UNIT, Destination.TRAUMA_CENTER, Destination.GENERAL_HOSPITAL):
        n = needs.get(dest, 0)
        if n > 0:
            parts.append(f"{n}x {_DEST_LABEL[dest]}")
    return ", ".join(parts) if parts else "1× General Hospital (default)"

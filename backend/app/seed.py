"""Demo seed data: hospitals (with doctor names), ambulances.

Does not create patients or emergencies. Coordinates are in Sofia, Bulgaria,
for sensible OSRM routing on the public demo server.

Usage:
  - Set env ``SEED_DEMO_DATA=1`` (or ``true`` / ``yes``) before starting uvicorn.
  - Or from ``backend/``: ``PYTHONPATH=. python -m app.seed``
  - CLI: ``python -m app.seed --replace`` clears hospitals and ambulances first
    (patients are left untouched).
"""

from __future__ import annotations

import argparse
import os

from app import database as db
from app.models import Ambulance, AmbulanceStatus, Hospital, Location

# Sofia — hospital sites near major facilities; OSRM demo covers the area well.
_SEED_HOSPITALS: list[Hospital] = [
    Hospital(
        hospital_id="H-SEED01",
        location=Location(latitude=42.6842, longitude=23.3167),
        doctors=[
            "Dr. Elena Petrova",
            "Dr. Nikolay Georgiev",
            "Dr. Mariya Stoyanova",
        ],
        burn_unit_beds_total=4,
        burn_unit_beds_available=4,
        trauma_center_beds_total=4,
        trauma_center_beds_available=4,
        general_beds_total=4,
        general_beds_available=4,
        patient_ids=[],
    ),
    Hospital(
        hospital_id="H-SEED02",
        location=Location(latitude=42.6769, longitude=23.3052),
        doctors=[
            "Dr. Ivan Dimitrov",
            "Dr. Stefka Atanasova",
        ],
        burn_unit_beds_total=3,
        burn_unit_beds_available=3,
        trauma_center_beds_total=3,
        trauma_center_beds_available=3,
        general_beds_total=2,
        general_beds_available=2,
        patient_ids=[],
    ),
    Hospital(
        hospital_id="H-SEED03",
        location=Location(latitude=42.6547, longitude=23.3644),
        doctors=[
            "Dr. Georgi Ivanov",
            "Dr. Rumyana Koleva",
            "Dr. Andrey Nikolov",
            "Dr. Vesela Todorova",
        ],
        burn_unit_beds_total=5,
        burn_unit_beds_available=5,
        trauma_center_beds_total=5,
        trauma_center_beds_available=5,
        general_beds_total=5,
        general_beds_available=5,
        patient_ids=[],
    ),
]

_SEED_AMBULANCES: list[Ambulance] = [
    Ambulance(
        ambulance_id="AMB-SEED01",
        location=Location(latitude=42.6856, longitude=23.3189),
        status=AmbulanceStatus.AVAILABLE,
    ),
    Ambulance(
        ambulance_id="AMB-SEED02",
        location=Location(latitude=42.6977, longitude=23.3219),
        status=AmbulanceStatus.AVAILABLE,
    ),
    Ambulance(
        ambulance_id="AMB-SEED03",
        location=Location(latitude=42.6660, longitude=23.3220),
        status=AmbulanceStatus.AVAILABLE,
    ),
    Ambulance(
        ambulance_id="AMB-SEED04",
        location=Location(latitude=42.6710, longitude=23.3080),
        status=AmbulanceStatus.AVAILABLE,
    ),
]


def apply_seed_data(*, replace: bool = False) -> None:
    """Insert seed hospitals and ambulances. Never modifies ``db.patients``.

    If ``replace`` is True, clears ``hospitals`` and ``ambulances`` first.
    If False, only adds records whose IDs are not already present.
    """
    if replace:
        db.hospitals.clear()
        db.ambulances.clear()

    for hospital in _SEED_HOSPITALS:
        if replace or hospital.hospital_id not in db.hospitals:
            db.hospitals[hospital.hospital_id] = hospital.model_copy(deep=True)

    for ambulance in _SEED_AMBULANCES:
        if replace or ambulance.ambulance_id not in db.ambulances:
            db.ambulances[ambulance.ambulance_id] = ambulance.model_copy(
                deep=True
            )


def _env_wants_seed() -> bool:
    v = os.getenv("SEED_DEMO_DATA", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def seed_on_startup_if_configured() -> None:
    """Call from FastAPI lifespan when ``SEED_DEMO_DATA`` is enabled.

    Clears the in-memory store (patients, hospitals, ambulances) then loads
    demo hospitals and ambulances so each start is a fresh seeded demo.
    """
    if _env_wants_seed():
        db.patients.clear()
        apply_seed_data(replace=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load demo seed data.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Clear hospitals and ambulances before seeding (patients unchanged).",
    )
    args = parser.parse_args()
    apply_seed_data(replace=args.replace)
    print(
        f"Seed complete: {len(db.hospitals)} hospitals, "
        f"{len(db.ambulances)} ambulances."
    )


if __name__ == "__main__":
    main()

"""In-memory data store.  Swap this module for a real DB adapter later."""

from app.models import Ambulance, Hospital, Patient

patients: dict[str, Patient] = {}
ambulances: dict[str, Ambulance] = {}
hospitals: dict[str, Hospital] = {}

"""In-memory data store.  Swap this module for a real DB adapter later."""

import asyncio

from app.models import Ambulance, Hospital, Patient

patients: dict[str, Patient] = {}
ambulances: dict[str, Ambulance] = {}
hospitals: dict[str, Hospital] = {}

# Protects compound read-modify-write operations on the shared dicts above.
# Acquire this whenever a handler needs to check state and then mutate it
# atomically (e.g. checking ambulance availability then assigning it).
lock = asyncio.Lock()

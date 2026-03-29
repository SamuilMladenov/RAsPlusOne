from contextlib import asynccontextmanager

import app.config  # noqa: F401 — load .env before auth accounts

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ambulances, auth, emergencies, hospitals, patients, ws
from app.seed import seed_on_startup_if_configured


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_on_startup_if_configured()
    yield


app = FastAPI(
    title="TriageFlow — Ambulance Dispatch System",
    description=(
        "Manage ambulances, patients and hospitals. "
        "Patients are assigned to ambulances which are routed to the "
        "nearest hospital using real road distances (OSRM)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ws.router)
app.include_router(patients.router)
app.include_router(ambulances.router)
app.include_router(hospitals.router)
app.include_router(emergencies.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "RAs+1 Ambulance Dispatch"}

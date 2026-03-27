from fastapi import FastAPI

from app.routers import ambulances, hospitals, patients

app = FastAPI(
    title="RAs+1 — Ambulance Dispatch System",
    description=(
        "Manage ambulances, patients and hospitals. "
        "Patients are assigned to ambulances which are routed to the "
        "nearest hospital using real road distances (OSRM)."
    ),
    version="0.1.0",
)

app.include_router(patients.router)
app.include_router(ambulances.router)
app.include_router(hospitals.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "RAs+1 Ambulance Dispatch"}

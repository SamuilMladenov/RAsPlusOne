# TriageFlow

## Introduction
TriageFlow is an end-to-end emergency medical triage system designed to streamline patient care from the field to the hospital. When a paramedic arrives at a scene, they complete a standardized triage form and scan it directly through the mobile app — at which point computer vision extracts and digitizes the patient's medical data automaticall. The processed information is then fed into an intelligent dispatch system that evaluates hospital availability and patient needs to assign the most suitable facility. An ambulance is coordinated for transport, and critically, the full patient profile — vitals, condition, and triage classification — is forwarded to the receiving hospital ahead of arrival, giving medical staff the time they need to prepare the right resources, the right team, and the right treatment before the patient even walks through the door.

## Triage Computer Vision

A computer vision pipeline that reads Mass Casualty Triage Cards from photos and outputs structured patient data. The system automatically detects which checkboxes are ticked, identifies the corresponding triage labels, and reads the patient ID using OCR — replacing manual data entry with a single photo.
 
### How it works
 
The pipeline processes each card in three stages:
 
1. **Region detection** — 21 fixed regions are cropped from the card photo based on positions learned from labeled training data
2. **Checkbox classification** — a binary classifier (Model A) determines whether each region is ticked or unticked
3. **Label identification** — ticked regions are routed to one of five section-specific models (Priority, Respiration, Perfusion, Mental Status, Destination), each enforcing mutual exclusivity within its section
4. **ID reading** — EasyOCR reads the numeric patient ID from the ID field region
 
The output is a structured JSON file containing the full triage assessment for each card.
 
---
 
### How to run
  
**Single card:**
```bash
python inference.py \
  --image      ./photos/IMG_0001.JPG \
  --models_dir ./runs/checkbox \
  --output_dir ./results
```
 
**Batch (entire folder):**
```bash
python inference.py \
  --image_dir  ./photos \
  --models_dir ./runs/checkbox \
  --output_dir ./results
```
 
Results are saved as JSON files in the output directory. Each card produces one file, and a combined `all_results.json` is generated for batch runs.
 
### Example output
 
```json
{
  "image": "IMG_0001.JPG",
  "id": "1021",
  "priority": "PRIORITY_RED",
  "respiration": "RESP_MORE_30",
  "perfusion": "PERF_SEVERE_BLEEDING",
  "mental_status": "MENTAL_UNRESPONSIVE",
  "destination": "DEST_TRAUMA_CENTER",
  "processing_time_ms": 944
}
```
 
---


## Dispatch Dashboard and Camera App

The Dispatch Dashboard is a core operational UI for emergency response coordination.
It connects real-time triage events (from mobile cameras/triage scans) to hospital capacity and ambulance availability, enabling automatic assignment and continuous hospital status updates.

## Backend (FastAPI)

Location: `backend/app`

- Primary service: `backend/app/main.py`
- Data models + routers are in:
  - `backend/app/models.py`
  - `backend/app/schemas.py`
  - `backend/app/routers/*` (ambulances, hospitals, emergencies, patients, triage, ws)
- Business logic services are in:
  - `backend/app/services/*` (dispatch queue, distance, hospital beds/dashboard, etc.)
- DB and auth setup:
  - `backend/app/database.py`
  - `backend/app/deps.py`
  - `backend/app/auth_accounts.py`

### Run backend

From project root:

```bash
cd backend
SEED_DEMO_DATA=1 uvicorn app.main:app --reload
```

- `SEED_DEMO_DATA=1` is optional and preloads sample demo data (ambulances, hospitals, patients, cases).
- API server starts with hot reload on `127.0.0.1:8000` by default.

## Frontend (Vite + React)

Location: `frontend`

- Main SPA entry: `frontend/src/main.jsx`
- App shell: `frontend/src/App.jsx`
- Key components:
  - `frontend/src/components/MapView.jsx`
  - `frontend/src/components/HospitalDashboard.jsx`
  - `frontend/src/components/EmergencyPanel.jsx`
  - `frontend/src/components/AmbulancePanel.jsx`
  - `frontend/src/components/PatientPanel.jsx`
  - `frontend/src/components/TriagePage.jsx`
- API client helper: `frontend/src/api.js`
- Auth + routing: `frontend/src/AuthContext.jsx`, `frontend/src/components/ProtectedRoute.jsx`

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend starts on Vite dev server, typically `http://localhost:5173`.
- Connects to backend endpoints (e.g., `/api/emergencies`, `/api/hospitals`, WebSocket path from `ws` router).

## End-to-end dispatch workflow

1. Triage card scan → CV pipeline extracts patient triage fields.
2. Extracted event posted to backend emergency router.
3. Dispatch service evaluates hospital bed availability + distance.
4. Dashboard updates:
   - Active emergencies
   - Assigned ambulances
   - Hospital capacity and incoming patients
5. Clinicians and dispatchers can track state and reroute in real time.

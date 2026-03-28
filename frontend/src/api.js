const BASE = "/api";

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ── Hospitals ──────────────────────────────────────────────────────
export const getHospitals = () => request("/hospitals/");
export const getHospitalDashboard = (hospitalId) =>
  request(`/hospitals/${hospitalId}/dashboard`);
export const createHospital = (data) =>
  request("/hospitals/", { method: "POST", body: JSON.stringify(data) });
export const deleteHospital = (id) =>
  request(`/hospitals/${id}`, { method: "DELETE" });

// ── Ambulances ─────────────────────────────────────────────────────
export const getAmbulances = () => request("/ambulances/");
export const createAmbulance = (data) =>
  request("/ambulances/", { method: "POST", body: JSON.stringify(data) });
export const updateAmbulance = (id, data) =>
  request(`/ambulances/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteAmbulance = (id) =>
  request(`/ambulances/${id}`, { method: "DELETE" });
export const assignPatient = (ambulanceId, patientId) =>
  request(`/ambulances/${ambulanceId}/assign-patient/${patientId}`, {
    method: "POST",
  });
export const assignNearestHospital = (ambulanceId) =>
  request(`/ambulances/${ambulanceId}/assign-hospital`, { method: "POST" });

// ── Patients ───────────────────────────────────────────────────────
export const getPatients = () => request("/patients/");
export const createPatient = (data) =>
  request("/patients/", { method: "POST", body: JSON.stringify(data) });
export const deletePatient = (id) =>
  request(`/patients/${id}`, { method: "DELETE" });
export const dispatchPatient = (id) =>
  request(`/patients/${id}/dispatch`, { method: "POST" });

// ── Emergencies ────────────────────────────────────────────────────
export const createEmergency = (data) =>
  request("/emergencies/", { method: "POST", body: JSON.stringify(data) });

const apiOrigin =
  typeof import.meta.env.VITE_API_URL === "string" &&
  import.meta.env.VITE_API_URL.trim() !== ""
    ? import.meta.env.VITE_API_URL.trim().replace(/\/$/, "")
    : "";

/** Dev: Vite proxies `/api` → backend. Production (e.g. Render): set `VITE_API_URL` to the API origin. */
const BASE = apiOrigin || "/api";

function authHeaders() {
  const t = localStorage.getItem("auth_token");
  const h = { "Content-Type": "application/json" };
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { ...authHeaders(), ...opts.headers },
    ...opts,
  });
  if (res.status === 401 && path !== "/auth/login") {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  if (res.status === 204) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export const getMe = () => request("/auth/me");

// ── Hospitals ──────────────────────────────────────────────────────
export const getHospitals = () => request("/hospitals/");
export const getHospitalDashboard = (hospitalId) =>
  request(`/hospitals/${hospitalId}/dashboard`);
export const createHospital = (data) =>
  request("/hospitals/", { method: "POST", body: JSON.stringify(data) });
export const deleteHospital = (id) =>
  request(`/hospitals/${id}`, { method: "DELETE" });
export const updateHospital = (id, data) =>
  request(`/hospitals/${id}`, { method: "PATCH", body: JSON.stringify(data) });

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

/** WebSocket URL for admin realtime events (`/ws`). Same host as HTTP API (Vite proxies `/ws` in dev). */
export function getEventsWebSocketUrl(token) {
  if (!token) return null;
  const q = `token=${encodeURIComponent(token)}`;
  if (apiOrigin) {
    const u = new URL(apiOrigin);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    u.pathname = "/ws";
    u.search = q;
    return u.toString();
  }
  if (typeof window === "undefined") return null;
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws?${q}`;
}

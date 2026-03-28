import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../AuthContext";
import * as api from "../api";

const LEG_LABELS = {
  to_patient: "Heading to patient",
  at_scene: "At scene",
  to_hospital: "Heading to hospital",
};

function triageDotClass(triage) {
  if (triage === "red") return "bg-red-500";
  if (triage === "yellow") return "bg-amber-500";
  if (triage === "black") return "bg-gray-800";
  return "bg-green-500";
}

function triageLabel(triage) {
  if (triage === "red") return "Red (immediate)";
  if (triage === "yellow") return "Yellow (urgent)";
  if (triage === "black") return "Black (expectant)";
  return "Green (minor)";
}

function formatLocation(loc) {
  if (!loc || loc.latitude == null || loc.longitude == null) return "—";
  return `${Number(loc.latitude).toFixed(4)}, ${Number(loc.longitude).toFixed(4)}`;
}

/** Backend sends ETA in minutes (often fractional); show whole minutes + seconds. */
function formatEtaMinSec(etaMinutes) {
  const m = Number(etaMinutes);
  if (!Number.isFinite(m) || m < 0) return null;
  const totalSeconds = Math.round(m * 60);
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  if (mins === 0) return `${secs} sec`;
  if (secs === 0) return `${mins} min`;
  return `${mins} min ${secs} sec`;
}

function formatOptional(v) {
  if (v == null || v === "") return "—";
  return String(v);
}

function PatientDetailCard({ patient, showAmbulance }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50/80 p-3 text-sm">
      <div className="flex flex-wrap gap-x-4 gap-y-2 items-start justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-gray-400">Patient ID</p>
          <p className="font-mono text-gray-900 font-medium">{patient.patient_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full shrink-0 ${triageDotClass(patient.triage_priority)}`} />
          <div>
            <p className="text-[10px] uppercase tracking-wide text-gray-400">Triage</p>
            <p className="text-gray-800">{triageLabel(patient.triage_priority)}</p>
          </div>
        </div>
      </div>
      <dl className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 text-xs">
        <div>
          <dt className="text-gray-400">Status</dt>
          <dd className="text-gray-800 capitalize">{formatOptional(patient.status)?.replace(/_/g, " ")}</dd>
        </div>
        <div>
          <dt className="text-gray-400">Destination</dt>
          <dd className="text-gray-800">{formatOptional(patient.destination)}</dd>
        </div>
        <div>
          <dt className="text-gray-400">Respiration</dt>
          <dd className="text-gray-800">{formatOptional(patient.respiration)}</dd>
        </div>
        <div>
          <dt className="text-gray-400">Perfusion</dt>
          <dd className="text-gray-800">{formatOptional(patient.perfusion)}</dd>
        </div>
        <div>
          <dt className="text-gray-400">Mental status</dt>
          <dd className="text-gray-800">{formatOptional(patient.mental_status)}</dd>
        </div>
        <div>
          <dt className="text-gray-400">Last known location</dt>
          <dd className="font-mono text-gray-700 tabular-nums">{formatLocation(patient.location)}</dd>
        </div>
        {showAmbulance && (
          <div className="sm:col-span-2">
            <dt className="text-gray-400">Ambulance</dt>
            <dd className="font-mono text-gray-800">{formatOptional(patient.ambulance_id)}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}

export default function HospitalDashboard() {
  const { hospitalId } = useParams();
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bedEdit, setBedEdit] = useState(null);
  const [bedSaving, setBedSaving] = useState(false);
  const [bedError, setBedError] = useState(null);
  const [bedSavedAt, setBedSavedAt] = useState(null);
  const [bedCapacityOpen, setBedCapacityOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const dash = await api.getHospitalDashboard(hospitalId);
      setData(dash);
      setError(null);
    } catch (e) {
      setError(e.message || "Failed to load dashboard");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [hospitalId]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  useEffect(() => {
    if (!data?.hospital) return;
    const h = data.hospital;
    setBedEdit({
      burn_unit_beds_total: h.burn_unit_beds_total,
      burn_unit_beds_available: h.burn_unit_beds_available,
      trauma_center_beds_total: h.trauma_center_beds_total,
      trauma_center_beds_available: h.trauma_center_beds_available,
      general_beds_total: h.general_beds_total,
      general_beds_available: h.general_beds_available,
    });
    setBedError(null);
  }, [data]);

  const setBedField = (key, raw) => {
    const n = parseInt(String(raw), 10);
    if (Number.isNaN(n) || n < 0) return;
    setBedEdit((prev) => (prev ? { ...prev, [key]: n } : prev));
  };

  const saveBeds = async () => {
    if (!bedEdit) return;
    setBedSaving(true);
    setBedError(null);
    setBedSavedAt(null);
    try {
      await api.updateHospital(hospitalId, bedEdit);
      await load();
      setBedSavedAt(Date.now());
    } catch (e) {
      setBedError(e.message || "Could not save");
    } finally {
      setBedSaving(false);
    }
  };

  const hasActiveIncoming =
    data?.incoming?.length > 0 &&
    data.incoming.some((row) =>
      ["en_route", "at_scene", "transporting"].includes(row.status),
    );

  const POLL_MS = 60_000;

  useEffect(() => {
    if (!hasActiveIncoming) return;
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [hasActiveIncoming, load]);

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-500 text-sm">
        Loading…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-gray-700 text-center">{error || "Hospital not found"}</p>
        <div className="flex flex-wrap gap-3 justify-center">
          {user?.role === "admin" && (
            <Link
              to="/"
              className="text-primary-600 font-medium text-sm hover:underline"
            >
              Back to dispatch
            </Link>
          )}
          <button
            type="button"
            onClick={logout}
            className="text-gray-600 font-medium text-sm hover:underline"
          >
            Log out
          </button>
        </div>
      </div>
    );
  }

  const { hospital, incoming, departments = [] } = data;
  const totalAvail =
    (hospital.burn_unit_beds_available ?? 0) +
    (hospital.trauma_center_beds_available ?? 0) +
    (hospital.general_beds_available ?? 0);
  const totalCap =
    (hospital.burn_unit_beds_total ?? 0) +
    (hospital.trauma_center_beds_total ?? 0) +
    (hospital.general_beds_total ?? 0);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">{hospital.hospital_id}</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Incoming ambulances · ETA refreshes about every minute (road, or straight-line if routing is busy)
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span
            className={
              totalAvail > 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"
            }
          >
            <span className="tabular-nums">
              Beds {totalAvail}/{totalCap}
            </span>{" "}
            free (all departments)
          </span>
          {user?.role === "admin" && (
            <Link
              to="/"
              className="text-primary-600 font-medium hover:underline"
            >
              Back to dispatch
            </Link>
          )}
          <span className="text-gray-400 hidden sm:inline">|</span>
          <span className="text-[11px] text-gray-500 truncate max-w-[200px]" title={user?.email}>
            {user?.email}
          </span>
          <button
            type="button"
            onClick={logout}
            className="text-gray-600 font-medium hover:text-red-600 text-sm"
          >
            Log out
          </button>
        </div>
      </header>

      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Free beds by department
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {departments.map((dept) => (
            <div
              key={dept.destination}
              className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
            >
              <p className="text-sm font-semibold text-gray-800">{dept.label}</p>
              <p
                className={`text-lg font-bold tabular-nums mt-1 ${
                  dept.beds_available > 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {dept.beds_available}/{dept.beds_total}
              </p>
              <p className="text-xs text-gray-500">free / capacity</p>
            </div>
          ))}
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-10">
        <section className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <button
            type="button"
            onClick={() => setBedCapacityOpen((o) => !o)}
            className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-gray-50/80 transition-colors"
            aria-expanded={bedCapacityOpen}
            aria-controls="bed-capacity-panel"
            id="bed-capacity-heading"
          >
            <span
              className={`shrink-0 text-gray-400 transition-transform duration-200 inline-block w-5 text-center ${
                bedCapacityOpen ? "rotate-180" : ""
              }`}
              aria-hidden
            >
              ▼
            </span>
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-semibold text-gray-800">Bed capacity</h2>
              {!bedCapacityOpen && (
                <p className="text-xs text-gray-500 mt-0.5 tabular-nums">
                  {totalAvail} / {totalCap} beds free · Burn, trauma, general
                </p>
              )}
            </div>
          </button>

          <div
            id="bed-capacity-panel"
            role="region"
            aria-labelledby="bed-capacity-heading"
            hidden={!bedCapacityOpen}
            className="border-t border-gray-100 px-5 pb-5"
          >
            <p className="text-xs text-gray-500 pt-4 mb-4">
              Set total capacity and how many beds are currently free for each unit. Totals
              cannot be less than available (the server will raise totals if needed).
            </p>
            {bedEdit ? (
              <div className="space-y-4">
                {[
                  {
                    key: "burn",
                    label: "Burn unit",
                    totalKey: "burn_unit_beds_total",
                    availKey: "burn_unit_beds_available",
                  },
                  {
                    key: "trauma",
                    label: "Trauma center",
                    totalKey: "trauma_center_beds_total",
                    availKey: "trauma_center_beds_available",
                  },
                  {
                    key: "general",
                    label: "General",
                    totalKey: "general_beds_total",
                    availKey: "general_beds_available",
                  },
                ].map((row) => (
                  <div
                    key={row.key}
                    className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3 items-end sm:items-center border-b border-gray-100 pb-4 last:border-0 last:pb-0"
                  >
                    <p className="text-sm font-medium text-gray-700">{row.label}</p>
                    <label className="block text-xs text-gray-500">
                      Total beds
                      <input
                        type="number"
                        min={0}
                        className="mt-1 block w-full sm:w-24 px-2 py-1.5 border border-gray-300 rounded-lg text-sm tabular-nums"
                        value={bedEdit[row.totalKey]}
                        onChange={(e) => setBedField(row.totalKey, e.target.value)}
                      />
                    </label>
                    <label className="block text-xs text-gray-500">
                      Available
                      <input
                        type="number"
                        min={0}
                        className="mt-1 block w-full sm:w-24 px-2 py-1.5 border border-gray-300 rounded-lg text-sm tabular-nums"
                        value={bedEdit[row.availKey]}
                        onChange={(e) => setBedField(row.availKey, e.target.value)}
                      />
                    </label>
                  </div>
                ))}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={saveBeds}
                    disabled={bedSaving}
                    className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
                  >
                    {bedSaving ? "Saving…" : "Save bed counts"}
                  </button>
                  {bedSavedAt && (
                    <span className="text-xs text-green-600 font-medium">Saved</span>
                  )}
                  {bedError && (
                    <span className="text-xs text-red-600">{bedError}</span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-400">Loading…</p>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Departments and admitted patients</h2>
          <p className="text-xs text-gray-500 mb-4">
            Patients listed by the bed type they were assigned (burn, trauma, or general). Occupancy reflects
            admitted patients currently at this hospital.
          </p>
          <div className="space-y-6">
            {departments.map((dept) => (
              <div
                key={dept.destination}
                className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden"
              >
                <div className="px-4 py-3 bg-gray-100 border-b border-gray-200 flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold text-gray-900">{dept.label}</h3>
                  <span className="text-sm text-gray-600 tabular-nums">
                    <span className={dept.beds_available > 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                      {dept.beds_available} free
                    </span>
                    <span className="text-gray-400"> · </span>
                    {dept.patients.length} admitted
                    <span className="text-gray-400"> · </span>
                    {dept.beds_total} beds
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  {dept.patients.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">No patients in this department right now.</p>
                  ) : (
                    dept.patients.map((p) => (
                      <PatientDetailCard key={p.patient_id} patient={p} showAmbulance={false} />
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Incoming ambulances</h2>
          {incoming.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white p-10 text-center text-gray-500 text-sm">
              No incoming ambulances assigned to this hospital right now.
            </div>
          ) : (
            <ul className="space-y-3">
              {incoming.map((row) => (
                <li
                  key={row.ambulance_id}
                  className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-gray-800">{row.ambulance_id}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {LEG_LABELS[row.leg] || row.leg}
                        <span className="text-gray-400"> · </span>
                        <span className="capitalize">{row.status.replace(/_/g, " ")}</span>
                      </p>
                    </div>
                    <div className="text-right">
                      {row.eta_minutes_to_hospital != null ? (
                        <>
                          <p className="text-lg font-bold text-primary-700 tabular-nums">
                            ~{formatEtaMinSec(row.eta_minutes_to_hospital) ?? row.eta_minutes_to_hospital}
                            {row.eta_approximate && (
                              <span className="text-xs font-normal text-amber-700 ml-1">(approx.)</span>
                            )}
                          </p>
                          {row.distance_km_remaining != null && (
                            <p className="text-xs text-gray-400 tabular-nums">
                              {row.distance_km_remaining} km
                            </p>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-amber-700 max-w-[220px]" title={row.eta_unavailable_reason || ""}>
                          ETA unavailable
                          {row.eta_unavailable_reason && (
                            <span className="block text-[10px] text-gray-400 font-normal mt-0.5 truncate">
                              {row.eta_unavailable_reason}
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                  {row.patients?.length > 0 && (
                    <div className="mt-4 border-t border-gray-100 pt-3">
                      <p className="text-xs font-semibold text-gray-600 mb-2">Patients on board</p>
                      <div className="space-y-3">
                        {row.patients.map((p) => (
                          <PatientDetailCard key={p.patient_id} patient={p} showAmbulance />
                        ))}
                      </div>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

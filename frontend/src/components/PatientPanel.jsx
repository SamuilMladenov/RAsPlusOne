import { useState } from "react";
import * as api from "../api";

const TRIAGE_STYLES = {
  red: "bg-red-100 text-red-700 border-red-200",
  yellow: "bg-amber-100 text-amber-700 border-amber-200",
  green: "bg-green-100 text-green-700 border-green-200",
};

const TRIAGE_DOT = {
  red: "bg-red-500",
  yellow: "bg-amber-500",
  green: "bg-green-500",
};

export default function PatientPanel({
  patients,
  ambulances,
  onRefresh,
  toast,
}) {
  const [triage, setTriage] = useState("green");
  const [loading, setLoading] = useState(false);
  const [dispatching, setDispatching] = useState(null);

  const handleCreate = async () => {
    setLoading(true);
    try {
      const res = await api.createPatient({ triage_status: triage });
      toast(`Patient "${res.patient_id}" created`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (pid) => {
    setDispatching(pid);
    try {
      const res = await api.dispatchPatient(pid);
      toast(
        `Dispatched! ${res.ambulance_id} → ${res.hospital_id} (${res.distance_km} km, ~${res.duration_minutes} min)`,
      );
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setDispatching(null);
    }
  };

  const handleDelete = async (pid) => {
    try {
      await api.deletePatient(pid);
      toast(`Deleted ${pid}`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const getAmbulance = (ambId) =>
    ambulances.find((a) => a.ambulance_id === ambId);

  return (
    <div className="space-y-4">
      {/* Create form */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Add Patient</h3>
        <div className="flex gap-2">
          {["red", "yellow", "green"].map((t) => (
            <button
              key={t}
              onClick={() => setTriage(t)}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                triage === t
                  ? TRIAGE_STYLES[t]
                  : "bg-white text-gray-400 border-gray-200"
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>
        <button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-2 text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Creating…" : "Create Patient"}
        </button>
      </div>

      {/* List */}
      <div className="space-y-2">
        {patients.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-4">
            No patients yet
          </p>
        )}
        {patients.map((p) => {
          const amb = p.ambulance_id ? getAmbulance(p.ambulance_id) : null;
          return (
            <div
              key={p.patient_id}
              className="rounded-lg border border-gray-200 bg-white p-3 space-y-2 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${TRIAGE_DOT[p.triage_status] || "bg-gray-400"}`}
                    title={`Triage: ${p.triage_status}`}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {p.patient_id}
                    </p>
                    {p.ambulance_id ? (
                      <p className="text-xs text-green-600 mt-0.5">
                        🚑 {p.ambulance_id}
                        {amb?.hospital_id && ` → ${amb.hospital_id}`}
                      </p>
                    ) : (
                      <p className="text-xs text-gray-400 mt-0.5">Unassigned</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${TRIAGE_STYLES[p.triage_status]}`}
                  >
                    {p.triage_status}
                  </span>
                  <button
                    onClick={() => handleDelete(p.patient_id)}
                    className="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none"
                    title="Delete"
                  >
                    ×
                  </button>
                </div>
              </div>

              {!p.ambulance_id && (
                <button
                  onClick={() => handleDispatch(p.patient_id)}
                  disabled={dispatching === p.patient_id}
                  className="w-full py-1.5 text-xs font-medium text-white bg-amber-500 hover:bg-amber-600 rounded-md transition-colors disabled:opacity-50"
                >
                  {dispatching === p.patient_id
                    ? "Dispatching…"
                    : "⚡ Auto-Dispatch"}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

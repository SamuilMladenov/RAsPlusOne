import { useState } from "react";
import * as api from "../api";

const TRIAGE_STYLES = {
  red: "bg-red-100 text-red-700 border-red-200",
  yellow: "bg-amber-100 text-amber-700 border-amber-200",
  green: "bg-green-100 text-green-700 border-green-200",
  black: "bg-gray-800 text-white border-gray-700",
};

const TRIAGE_DOT = {
  red: "bg-red-500",
  yellow: "bg-amber-500",
  green: "bg-green-500",
  black: "bg-gray-800",
};

const STATUS_STYLES = {
  waiting: "bg-orange-100 text-orange-700",
  in_transit: "bg-blue-100 text-blue-700",
  admitted: "bg-violet-100 text-violet-700",
};

const STATUS_LABELS = {
  waiting: "Waiting",
  in_transit: "In transit",
  admitted: "Admitted",
};

/** Matches backend Destination enum values */
const DESTINATION_OPTIONS = [
  { value: "", label: "General (default)" },
  { value: "General Hospital", label: "General Hospital" },
  { value: "Trauma Center", label: "Trauma Center" },
  { value: "Burn Unit", label: "Burn Unit" },
];

export default function PatientPanel({
  patients,
  ambulances,
  clickedLocation,
  onRefresh,
  toast,
}) {
  const [triage, setTriage] = useState("green");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!clickedLocation)
      return toast("Click the map to set the patient location", "error");
    setLoading(true);
    try {
      const payload = {
        location: clickedLocation,
        triage_priority: triage,
      };
      if (destination) payload.destination = destination;
      const res = await api.createPatient(payload);
      toast(`Patient "${res.patient_id}" created`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
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
          {["red", "yellow", "green", "black"].map((t) => (
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
        <div>
          <label className="block text-[10px] font-medium text-gray-500 mb-1">
            Destination (dispatch sends to a hospital with matching beds)
          </label>
          <select
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          >
            {DESTINATION_OPTIONS.map((o) => (
              <option key={o.label} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <p className="text-xs text-gray-400">
          📍 Click the map to set the patient location. An available ambulance is
          assigned automatically (red before yellow before green; closest ambulance
          first; up to two greens at the same spot with the same destination may
          share one ambulance).
        </p>
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
                    className={`w-2.5 h-2.5 rounded-full ${TRIAGE_DOT[p.triage_priority] || "bg-gray-400"}`}
                    title={`Triage: ${p.triage_priority}`}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {p.patient_id}
                    </p>
                    {p.status === "admitted" ? (
                      <p className="text-xs text-violet-600 mt-0.5">
                        🏥 Admitted
                      </p>
                    ) : p.ambulance_id ? (
                      <p className="text-xs text-blue-600 mt-0.5">
                        🚑 {p.ambulance_id}
                        {amb?.hospital_id && ` → ${amb.hospital_id}`}
                      </p>
                    ) : (
                      <p className="text-xs text-orange-500 mt-0.5">Waiting for dispatch</p>
                    )}
                    {p.destination && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        → {p.destination}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${TRIAGE_STYLES[p.triage_priority]}`}
                  >
                    {p.triage_priority}
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

              {p.status && (
                <span
                  className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase ${STATUS_STYLES[p.status] || "bg-gray-100 text-gray-600"}`}
                >
                  {STATUS_LABELS[p.status] || p.status}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

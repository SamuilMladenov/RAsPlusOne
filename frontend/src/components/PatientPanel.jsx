import { useState } from "react";
import * as api from "../api";

export default function PatientPanel({
  patients,
  ambulances,
  onRefresh,
  toast,
}) {
  const [id, setId] = useState("");
  const [loading, setLoading] = useState(false);
  const [dispatching, setDispatching] = useState(null);

  const handleCreate = async () => {
    if (!id.trim()) return toast("Enter a patient ID", "error");
    setLoading(true);
    try {
      await api.createPatient({ patient_id: id.trim() });
      toast(`Patient "${id.trim()}" created`);
      setId("");
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
        <input
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="Patient ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
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
                <button
                  onClick={() => handleDelete(p.patient_id)}
                  className="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none"
                  title="Delete"
                >
                  ×
                </button>
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

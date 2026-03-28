import { useState } from "react";
import * as api from "../api";

const STATUS_COLORS = {
  available: "bg-green-100 text-green-700",
  en_route: "bg-amber-100 text-amber-700",
  at_scene: "bg-red-100 text-red-700",
  transporting: "bg-violet-100 text-violet-700",
  at_hospital: "bg-blue-100 text-blue-700",
  out_of_service: "bg-gray-100 text-gray-600",
};

export default function AmbulancePanel({
  ambulances,
  patients,
  clickedLocation,
  onRefresh,
  toast,
}) {
  const [loading, setLoading] = useState(false);
  const [assigningHospital, setAssigningHospital] = useState(null);

  const handleCreate = async () => {
    if (!clickedLocation)
      return toast("Click the map to set a location", "error");
    setLoading(true);
    try {
      const res = await api.createAmbulance({
        location: clickedLocation,
      });
      toast(`Ambulance "${res.ambulance_id}" created`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAssignHospital = async (ambId) => {
    setAssigningHospital(ambId);
    try {
      const res = await api.assignNearestHospital(ambId);
      toast(
        `Assigned to ${res.hospital_id} (${res.distance_km} km, ~${res.duration_minutes} min)`,
      );
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setAssigningHospital(null);
    }
  };

  const handleDelete = async (ambId) => {
    try {
      await api.deleteAmbulance(ambId);
      toast(`Deleted ${ambId}`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const handleAssignPatient = async (ambId, patientId) => {
    try {
      await api.assignPatient(ambId, patientId);
      toast(`Patient ${patientId} assigned to ${ambId}`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const unassignedPatients = patients.filter((p) => !p.ambulance_id);

  return (
    <div className="space-y-4">
      {/* Create form */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Add Ambulance</h3>
        <p className="text-xs text-gray-400">
          📍 Click the map to pick a location
        </p>
        <button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-2 text-sm font-medium text-white bg-green-500 hover:bg-green-600 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Creating…" : "Create Ambulance"}
        </button>
      </div>

      {/* List */}
      <div className="space-y-2">
        {ambulances.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-4">
            No ambulances yet
          </p>
        )}
        {ambulances.map((a) => (
          <div
            key={a.ambulance_id}
            className="rounded-lg border border-gray-200 bg-white p-3 space-y-2 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {a.ambulance_id}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {a.location.latitude.toFixed(4)},{" "}
                  {a.location.longitude.toFixed(4)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[a.status]}`}
                >
                  {a.status.replace(/_/g, " ")}
                </span>
                <button
                  onClick={() => handleDelete(a.ambulance_id)}
                  className="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none"
                  title="Delete"
                >
                  ×
                </button>
              </div>
            </div>

            {a.hospital_id && (
              <p className="text-xs text-blue-500">
                → Hospital: {a.hospital_id}
              </p>
            )}

            {a.patient_ids.length > 0 && (
              <p className="text-xs text-gray-500">
                Patients: {a.patient_ids.join(", ")}
              </p>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => handleAssignHospital(a.ambulance_id)}
                disabled={assigningHospital === a.ambulance_id}
                className="flex-1 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors disabled:opacity-50"
              >
                {assigningHospital === a.ambulance_id
                  ? "Finding…"
                  : "Nearest Hospital"}
              </button>

              {unassignedPatients.length > 0 && (
                <select
                  onChange={(e) => {
                    if (e.target.value)
                      handleAssignPatient(a.ambulance_id, e.target.value);
                    e.target.value = "";
                  }}
                  defaultValue=""
                  className="flex-1 py-1.5 text-xs border border-gray-200 rounded-md bg-white text-gray-600 outline-none"
                >
                  <option value="" disabled>
                    + Assign patient
                  </option>
                  {unassignedPatients.map((p) => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.patient_id}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api";

export default function HospitalPanel({
  hospitals,
  patients,
  clickedLocation,
  onRefresh,
  toast,
}) {
  const [doctors, setDoctors] = useState("");
  const [beds, setBeds] = useState("10");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!clickedLocation) return toast("Click the map to set a location", "error");
    setLoading(true);
    try {
      const n = parseInt(beds, 10) || 0;
      const res = await api.createHospital({
        location: clickedLocation,
        doctors: doctors
          .split(",")
          .map((d) => d.trim())
          .filter(Boolean),
        total_beds: n,
        available_beds: n,
      });
      toast(`Hospital "${res.hospital_id}" created`);
      setDoctors("");
      setBeds("10");
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (hid) => {
    try {
      await api.deleteHospital(hid);
      toast(`Deleted ${hid}`);
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  return (
    <div className="space-y-4">
      {/* Create form */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Add Hospital</h3>
        <input
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="Doctors (comma-separated)"
          value={doctors}
          onChange={(e) => setDoctors(e.target.value)}
        />
        <input
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="Total bed capacity"
          type="number"
          min="0"
          value={beds}
          onChange={(e) => setBeds(e.target.value)}
        />
        <p className="text-xs text-gray-400">
          📍 Click the map to pick a location
        </p>
        <button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Creating…" : "Create Hospital"}
        </button>
      </div>

      {/* List */}
      <div className="space-y-2">
        {hospitals.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-4">
            No hospitals yet
          </p>
        )}
        {hospitals.map((h) => (
          <div
            key={h.hospital_id}
            className="rounded-lg border border-gray-200 bg-white p-3 flex items-start justify-between group hover:shadow-sm transition-shadow"
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-medium text-gray-800">
                  {h.hospital_id}
                </p>
                <Link
                  to={`/hospital/${h.hospital_id}`}
                  className="text-[11px] font-medium text-primary-600 hover:text-primary-700 hover:underline"
                >
                  Dashboard
                </Link>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                {h.location.latitude.toFixed(4)},{" "}
                {h.location.longitude.toFixed(4)}
              </p>
              <p className="text-xs mt-1">
                <span className={`font-medium tabular-nums ${h.available_beds > 0 ? "text-green-600" : "text-red-500"}`}>
                  🛏️ {h.available_beds}/{h.total_beds ?? h.available_beds} beds free
                </span>
              </p>
              {h.doctors.length > 0 && (
                <p className="text-xs text-gray-500 mt-0.5">
                  👨‍⚕️ {h.doctors.join(", ")}
                </p>
              )}
              {h.patient_ids.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {h.patient_ids.map((pid) => {
                    const pt = patients.find((p) => p.patient_id === pid);
                    const dotColor = pt?.triage_status === "red" ? "bg-red-500" : pt?.triage_status === "yellow" ? "bg-amber-500" : "bg-green-500";
                    return (
                      <span key={pid} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600">
                        <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
                        {pid}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
            <button
              onClick={() => handleDelete(h.hospital_id)}
              className="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none"
              title="Delete"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

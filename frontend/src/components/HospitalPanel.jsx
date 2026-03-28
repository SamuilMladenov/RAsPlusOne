import { useState } from "react";
import * as api from "../api";

export default function HospitalPanel({
  hospitals,
  clickedLocation,
  onRefresh,
  toast,
}) {
  const [id, setId] = useState("");
  const [doctors, setDoctors] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!id.trim()) return toast("Enter a hospital ID", "error");
    if (!clickedLocation) return toast("Click the map to set a location", "error");
    setLoading(true);
    try {
      await api.createHospital({
        hospital_id: id.trim(),
        location: clickedLocation,
        doctors: doctors
          .split(",")
          .map((d) => d.trim())
          .filter(Boolean),
      });
      toast(`Hospital "${id.trim()}" created`);
      setId("");
      setDoctors("");
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
          placeholder="Hospital ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
        <input
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="Doctors (comma-separated)"
          value={doctors}
          onChange={(e) => setDoctors(e.target.value)}
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
              <p className="text-sm font-medium text-gray-800">
                {h.hospital_id}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                {h.location.latitude.toFixed(4)},{" "}
                {h.location.longitude.toFixed(4)}
              </p>
              {h.doctors.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  👨‍⚕️ {h.doctors.join(", ")}
                </p>
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

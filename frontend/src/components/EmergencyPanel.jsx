import { useState } from "react";
import * as api from "../api";

export default function EmergencyPanel({
  clickedLocation,
  ambulances,
  hospitals,
  onRefresh,
  toast,
}) {
  const [count, setCount] = useState("1");
  const [loading, setLoading] = useState(false);

  const availableAmbulances = ambulances.filter(
    (a) => a.status === "available",
  ).length;
  const totalBeds = hospitals.reduce(
    (s, h) =>
      s +
      (h.burn_unit_beds_available ?? 0) +
      (h.trauma_center_beds_available ?? 0) +
      (h.general_beds_available ?? 0),
    0,
  );

  const handleEmergency = async () => {
    if (!clickedLocation)
      return toast("Click the map to set the emergency location", "error");
    const n = parseInt(count, 10);
    if (!n || n < 1) return toast("Enter a valid patient count", "error");

    setLoading(true);
    try {
      const res = await api.createEmergency({
        location: clickedLocation,
        patient_count: n,
      });
      const d = res.dispatched.length;
      const u = res.unassigned_patients.length;
      let msg = `Emergency created — ${d} ambulance${d !== 1 ? "s" : ""} dispatched`;
      if (u > 0) msg += `, ${u} patient${u !== 1 ? "s" : ""} unassigned`;
      toast(msg, u > 0 ? "error" : "success");
      onRefresh();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border-2 border-red-200 bg-red-50 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🚨</span>
          <h3 className="text-base font-bold text-red-700">
            Emergency Event
          </h3>
        </div>

        <p className="text-xs text-red-600">
          Creates patients at the scene with random triage and destination. Dispatch
          order is red, then yellow, then green; red and yellow travel one per
          ambulance, green up to two per ambulance when destination and location
          match. The nearest available ambulance to the scene is chosen first.
          Hospitals must have matching free beds.
        </p>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Number of patients
          </label>
          <input
            className="w-full px-3 py-2.5 text-sm border border-red-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-red-400 outline-none bg-white"
            type="number"
            min="1"
            value={count}
            onChange={(e) => setCount(e.target.value)}
          />
        </div>

        {clickedLocation ? (
          <div className="px-3 py-2 rounded-lg bg-white border border-red-200 text-xs text-red-700 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
            Location: {clickedLocation.latitude.toFixed(4)},{" "}
            {clickedLocation.longitude.toFixed(4)}
          </div>
        ) : (
          <div className="px-3 py-2 rounded-lg bg-white border border-gray-200 text-xs text-gray-400">
            📍 Click the map to set emergency location
          </div>
        )}

        <button
          onClick={handleEmergency}
          disabled={loading || !clickedLocation}
          className="w-full py-3 text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-40 tracking-wide"
        >
          {loading ? "Dispatching…" : "🚨 TRIGGER EMERGENCY"}
        </button>
      </div>

      {/* Status readout */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <p className="text-2xl font-bold text-green-600">
            {availableAmbulances}
          </p>
          <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-1">
            Ambulances ready
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <p className="text-2xl font-bold text-blue-600">{totalBeds}</p>
          <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-1">
            Beds available
          </p>
        </div>
      </div>
    </div>
  );
}

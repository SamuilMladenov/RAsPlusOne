import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "../api";

const LEG_LABELS = {
  to_patient: "Heading to patient",
  at_scene: "At scene",
  to_hospital: "Heading to hospital",
};

function triageDotClass(triage) {
  if (triage === "red") return "bg-red-500";
  if (triage === "yellow") return "bg-amber-500";
  return "bg-green-500";
}

function triageLabel(triage) {
  if (triage === "red") return "Red (immediate)";
  if (triage === "yellow") return "Yellow (urgent)";
  return "Green (minor)";
}

function formatLocation(loc) {
  if (!loc || loc.latitude == null || loc.longitude == null) return "—";
  return `${Number(loc.latitude).toFixed(4)}, ${Number(loc.longitude).toFixed(4)}`;
}

export default function HospitalDashboard() {
  const { hospitalId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

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
        <Link
          to="/"
          className="text-primary-600 font-medium text-sm hover:underline"
        >
          Back to dispatch
        </Link>
      </div>
    );
  }

  const { hospital, incoming } = data;
  const totalBeds = hospital.total_beds ?? hospital.available_beds;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">{hospital.hospital_id}</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Incoming ambulances · ETA refreshes about every minute (road, or straight-line if routing is busy)
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span
            className={
              hospital.available_beds > 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"
            }
          >
            <span className="tabular-nums">
              Beds {hospital.available_beds}/{totalBeds}
            </span>{" "}
            free
          </span>
          <Link
            to="/"
            className="text-primary-600 font-medium hover:underline"
          >
            Back to dispatch
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
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
                          ~{row.eta_minutes_to_hospital} min
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
                    {/* Future: name, chief complaint, vitals — extend API + this list */}
                    <ul className="rounded-lg border border-gray-200 overflow-hidden divide-y divide-gray-100">
                      {row.patients.map((p) => (
                        <li
                          key={p.patient_id}
                          className="px-3 py-2.5 bg-white text-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="text-[10px] uppercase tracking-wide text-gray-400">Patient ID</p>
                            <p className="font-mono text-gray-900 truncate">{p.patient_id}</p>
                          </div>
                          <div className="flex items-center gap-2 sm:w-48 shrink-0">
                            <span className={`w-2 h-2 rounded-full shrink-0 ${triageDotClass(p.triage_status)}`} />
                            <div>
                              <p className="text-[10px] uppercase tracking-wide text-gray-400">Triage</p>
                              <p className="text-gray-800">{triageLabel(p.triage_status)}</p>
                            </div>
                          </div>
                          <div className="sm:text-right sm:min-w-[10rem]">
                            <p className="text-[10px] uppercase tracking-wide text-gray-400">Last known location</p>
                            <p className="font-mono text-xs text-gray-600 tabular-nums">{formatLocation(p.location)}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

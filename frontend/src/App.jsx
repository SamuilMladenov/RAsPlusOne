import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";
import * as api from "./api";

function usePatientsRealtime(refresh, token, isAdmin) {
  useEffect(() => {
    if (!token || !isAdmin) return;
    let ws = null;
    let reconnectTimer = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const url = api.getEventsWebSocketUrl(token);
      if (!url) return;
      ws = new WebSocket(url);
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === "patients_updated") refresh();
        } catch {
          /* ignore */
        }
      };
      ws.onclose = () => {
        if (cancelled) return;
        reconnectTimer = window.setTimeout(connect, 3000);
      };
    };

    connect();
    return () => {
      cancelled = true;
      if (reconnectTimer != null) window.clearTimeout(reconnectTimer);
      if (ws != null && ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, [token, isAdmin, refresh]);
}

function ToastContainer({ toasts, dismiss }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          onClick={() => dismiss(t.id)}
          className={`px-4 py-3 rounded-xl shadow-lg text-sm cursor-pointer transition-all animate-slide-in ${
            t.type === "error"
              ? "bg-red-600 text-white"
              : "bg-primary-800 text-white"
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const { user, logout, token } = useAuth();
  const [hospitals, setHospitals] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [patients, setPatients] = useState([]);
  const [clickedLocation, setClickedLocation] = useState(null);
  const [toasts, setToasts] = useState([]);

  const toast = useCallback((message, type = "success") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [h, a, p] = await Promise.all([
        api.getHospitals(),
        api.getAmbulances(),
        api.getPatients(),
      ]);
      setHospitals(h);
      setAmbulances(a);
      setPatients(p);
    } catch (e) {
      toast("Failed to fetch data: " + e.message, "error");
    }
  }, [toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  usePatientsRealtime(refresh, token, user?.role === "admin");

  // Auto-poll while any ambulance is actively travelling (3s to reduce API load vs 1s)
  useEffect(() => {
    const hasMoving = ambulances.some(
      (a) =>
        a.status === "transporting" ||
        a.status === "en_route" ||
        a.status === "at_scene",
    );
    if (!hasMoving) return;
    const id = setInterval(refresh, 1000);
    return () => clearInterval(id);
  }, [ambulances, refresh]);

  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar
        hospitals={hospitals}
        ambulances={ambulances}
        patients={patients}
        clickedLocation={clickedLocation}
        onRefresh={refresh}
        toast={toast}
        user={user}
        onLogout={logout}
      />
      <div className="flex-1 relative">
        <MapView
          hospitals={hospitals}
          ambulances={ambulances}
          patients={patients}
          onMapClick={setClickedLocation}
          clickedLocation={clickedLocation}
        />
      </div>
      <ToastContainer toasts={toasts} dismiss={dismissToast} />

      <style>{`
        @keyframes slide-in {
          from { opacity: 0; transform: translateX(100px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

import { useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";

const STATUS_COLORS = {
  available: "#22c55e",
  en_route: "#f59e0b",
  at_scene: "#ef4444",
  transporting: "#8b5cf6",
  at_hospital: "#3b82f6",
  out_of_service: "#6b7280",
};

function svgIcon(svg, size = 36) {
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

function hospitalIcon() {
  return svgIcon(`
    <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="18" cy="18" r="16" fill="#ef4444" stroke="#fff" stroke-width="2"/>
      <path d="M14 12h8v4h4v8h-4v4h-8v-4h-4v-8h4z" fill="#fff"/>
    </svg>
  `);
}

function ambulanceIcon(status) {
  const color = STATUS_COLORS[status] || "#6b7280";
  return svgIcon(`
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="8" width="36" height="22" rx="4" fill="${color}" stroke="#fff" stroke-width="2"/>
      <path d="M17 14v4h-4v3h4v4h3v-4h4v-3h-4v-4z" fill="#fff"/>
      <circle cx="11" cy="30" r="3" fill="#fff" stroke="${color}" stroke-width="1.5"/>
      <circle cx="29" cy="30" r="3" fill="#fff" stroke="${color}" stroke-width="1.5"/>
    </svg>
  `, 40);
}

const TRIAGE_MARKER_COLORS = {
  red: "#ef4444",
  yellow: "#f59e0b",
  green: "#22c55e",
  black: "#1f2937",
};

function patientIcon(triage) {
  const color = TRIAGE_MARKER_COLORS[triage] || "#6b7280";
  return svgIcon(`
    <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="14" cy="14" r="12" fill="${color}" stroke="#fff" stroke-width="2"/>
      <circle cx="14" cy="10" r="3" fill="#fff"/>
      <path d="M8 20c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="#fff" stroke-width="2" fill="none"/>
    </svg>
  `, 28);
}

function clickIcon() {
  return svgIcon(`
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="#6366f1" fill-opacity="0.3" stroke="#6366f1" stroke-width="2"/>
      <circle cx="12" cy="12" r="4" fill="#6366f1"/>
    </svg>
  `, 24);
}

function ClickCapture({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick({ latitude: e.latlng.lat, longitude: e.latlng.lng });
    },
  });
  return null;
}

function FitBounds({ hospitals, ambulances }) {
  const map = useMap();
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current) return;
    const points = [
      ...hospitals.map((h) => [h.location.latitude, h.location.longitude]),
      ...ambulances.map((a) => [a.location.latitude, a.location.longitude]),
    ];
    if (points.length > 0) {
      map.fitBounds(points, { padding: [60, 60], maxZoom: 13 });
      fitted.current = true;
    }
  }, [hospitals, ambulances, map]);

  return null;
}

export default function MapView({
  hospitals,
  ambulances,
  patients,
  onMapClick,
  clickedLocation,
}) {
  return (
    <MapContainer
      center={[42.7, 23.32]}
      zoom={8}
      className="h-full w-full z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <ClickCapture onMapClick={onMapClick} />
      <FitBounds hospitals={hospitals} ambulances={ambulances} />

      {hospitals.map((h) => (
        <Marker
          key={`h-${h.hospital_id}`}
          position={[h.location.latitude, h.location.longitude]}
          icon={hospitalIcon()}
        >
          <Popup>
            <div className="text-sm">
              <p className="font-bold text-red-600">{h.hospital_id}</p>
              <p className="text-gray-500">
                {h.doctors.length} doctor{h.doctors.length !== 1 && "s"}
              </p>
              <p className={`text-xs font-medium ${h.available_beds > 0 ? "text-green-600" : "text-red-500"}`}>
                {h.available_beds} bed{h.available_beds !== 1 && "s"} available
              </p>
              {h.patient_ids.length > 0 && (
                <p className="text-xs text-violet-600">
                  {h.patient_ids.length} patient{h.patient_ids.length !== 1 && "s"} admitted
                </p>
              )}
              <p className="text-xs text-gray-400">
                {h.location.latitude.toFixed(4)},{" "}
                {h.location.longitude.toFixed(4)}
              </p>
            </div>
          </Popup>
        </Marker>
      ))}

      {ambulances.map((a) => (
        <Marker
          key={`a-${a.ambulance_id}`}
          position={[a.location.latitude, a.location.longitude]}
          icon={ambulanceIcon(a.status)}
        >
          <Popup>
            <div className="text-sm">
              <p className="font-bold" style={{ color: STATUS_COLORS[a.status] }}>
                {a.ambulance_id}
              </p>
              <p>
                Status:{" "}
                <span className="font-medium">{a.status.replace(/_/g, " ")}</span>
              </p>
              {a.hospital_id && (
                <p className="text-xs text-gray-500">→ {a.hospital_id}</p>
              )}
              {a.patient_ids.length > 0 && (
                <p className="text-xs text-gray-500">
                  Patients: {a.patient_ids.join(", ")}
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}

      {patients
        .filter((p) => p.location && !p.ambulance_id)
        .map((p) => (
          <Marker
            key={`p-${p.patient_id}`}
            position={[p.location.latitude, p.location.longitude]}
            icon={patientIcon(p.triage_priority)}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-bold">{p.patient_id}</p>
                <p className="text-xs uppercase font-medium" style={{ color: TRIAGE_MARKER_COLORS[p.triage_priority] }}>
                  Triage: {p.triage_priority}
                </p>
                <p className="text-xs text-gray-400">Waiting for pickup</p>
              </div>
            </Popup>
          </Marker>
        ))}

      {clickedLocation && (
        <Marker
          position={[clickedLocation.latitude, clickedLocation.longitude]}
          icon={clickIcon()}
        >
          <Popup>
            <span className="text-xs text-indigo-600 font-medium">
              Selected: {clickedLocation.latitude.toFixed(4)},{" "}
              {clickedLocation.longitude.toFixed(4)}
            </span>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}

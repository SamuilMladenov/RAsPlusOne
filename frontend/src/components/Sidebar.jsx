import { useState } from "react";
import HospitalPanel from "./HospitalPanel";
import AmbulancePanel from "./AmbulancePanel";
import PatientPanel from "./PatientPanel";
import EmergencyPanel from "./EmergencyPanel";

const TABS = [
  { key: "emergency", label: "Emergency", icon: "🚨" },
  { key: "hospitals", label: "Hospitals", icon: "🏥" },
  { key: "ambulances", label: "Ambulances", icon: "🚑" },
  { key: "patients", label: "Patients", icon: "🧑" },
];

export default function Sidebar({
  hospitals,
  ambulances,
  patients,
  clickedLocation,
  onRefresh,
  toast,
  user,
  onLogout,
}) {
  const [activeTab, setActiveTab] = useState("emergency");

  return (
    <div className="w-[380px] h-full flex flex-col bg-white border-r border-gray-200 shadow-xl z-10">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">
              RAs+1 Dispatch
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Ambulance management system
            </p>
          </div>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="text-[11px] font-medium text-gray-500 hover:text-red-600 px-2 py-1 rounded border border-gray-200 shrink-0"
            >
              Log out
            </button>
          )}
        </div>
        {user?.email && (
          <p className="text-[10px] text-indigo-600 mt-2 truncate" title={user.email}>
            {user.role === "admin" ? "Admin" : "Hospital"} · {user.email}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 px-2">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors relative ${
              activeTab === tab.key
                ? "text-primary-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
            {activeTab === tab.key && (
              <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-primary-600 rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Location badge */}
      {clickedLocation && (
        <div className="mx-4 mt-3 px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-xs text-indigo-700 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500 inline-block" />
          Selected: {clickedLocation.latitude.toFixed(4)},{" "}
          {clickedLocation.longitude.toFixed(4)}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto sidebar px-4 py-3">
        {activeTab === "emergency" && (
          <EmergencyPanel
            clickedLocation={clickedLocation}
            ambulances={ambulances}
            hospitals={hospitals}
            onRefresh={onRefresh}
            toast={toast}
          />
        )}
        {activeTab === "hospitals" && (
          <HospitalPanel
            hospitals={hospitals}
            patients={patients}
            clickedLocation={clickedLocation}
            onRefresh={onRefresh}
            toast={toast}
          />
        )}
        {activeTab === "ambulances" && (
          <AmbulancePanel
            ambulances={ambulances}
            patients={patients}
            clickedLocation={clickedLocation}
            onRefresh={onRefresh}
            toast={toast}
          />
        )}
        {activeTab === "patients" && (
          <PatientPanel
            patients={patients}
            ambulances={ambulances}
            clickedLocation={clickedLocation}
            onRefresh={onRefresh}
            toast={toast}
          />
        )}
      </div>

      {/* Footer stats */}
      <div className="px-5 py-3 border-t border-gray-100 bg-gray-50 flex justify-between text-xs text-gray-400">
        <span>{hospitals.length} hospitals</span>
        <span>{ambulances.length} ambulances</span>
        <span>{patients.length} patients</span>
      </div>
    </div>
  );
}

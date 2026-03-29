import { useState } from "react";
import BrandLogo from "./BrandLogo";
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
    <div className="w-[380px] h-full flex flex-col bg-white border-r border-primary-100 shadow-xl z-10">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <BrandLogo className="max-w-[240px]" />
            <p className="text-[10px] tracking-[0.12em] text-primary-700 font-medium uppercase mt-2">
              Dispatch
            </p>
          </div>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="text-[11px] font-medium text-primary-700 hover:text-red-600 px-2 py-1 rounded-lg border border-primary-200 hover:border-red-200 shrink-0 transition-colors"
            >
              Log out
            </button>
          )}
        </div>
        {user?.email && (
          <p className="text-[10px] text-primary-600 mt-2 truncate" title={user.email}>
            {user.role === "admin" ? "Admin" : "Hospital"} · {user.email}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-primary-100 px-2">
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
        <div className="mx-4 mt-3 px-3 py-2 rounded-xl bg-primary-50 border border-primary-200 text-xs text-primary-800 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary-500 inline-block" />
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

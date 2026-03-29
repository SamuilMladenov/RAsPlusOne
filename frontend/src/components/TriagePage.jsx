import { useCallback, useRef, useState } from "react";
import { useAuth } from "../AuthContext";
import * as api from "../api";
import BrandLogo from "./BrandLogo";

export default function TriagePage() {
  const { logout, user } = useAuth();
  const inputRef = useRef(null);
  const [phase, setPhase] = useState("idle");
  const [error, setError] = useState("");

  const openCamera = useCallback(() => {
    setError("");
    setPhase("idle");
    inputRef.current?.click();
  }, []);

  const onFileChange = useCallback(async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setError("");
    setPhase("uploading");
    try {
      await api.uploadTriagePhoto(file);
      setPhase("success");
    } catch (err) {
      setPhase("idle");
      setError(err.message || "Upload failed");
    }
  }, []);

  const nextPatient = useCallback(() => {
    setPhase("idle");
    setError("");
  }, []);

  return (
    <div className="min-h-[100dvh] flex flex-col bg-gradient-to-b from-slate-50 via-white to-primary-50 text-primary-900">
      <header className="shrink-0 px-4 pb-3 pt-[max(1rem,env(safe-area-inset-top))] border-b border-primary-100 bg-white/90 backdrop-blur-sm flex items-center justify-between gap-3 shadow-sm shadow-primary-900/5">
        <div className="flex items-center gap-2 min-w-0">
          <BrandLogo size="compact" className="shrink-0" />
          <div className="min-w-0">
            <h1 className="text-sm font-semibold text-primary-800 truncate">Triage capture</h1>
            {user?.email && (
              <p className="text-xs text-primary-600/80 truncate">{user.email}</p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={logout}
          className="shrink-0 text-xs font-medium text-primary-700 hover:text-primary-900 px-3 py-2 rounded-lg border border-primary-200 hover:border-primary-400 bg-white transition-colors"
        >
          Sign out
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-5 py-8 gap-6">
        {phase === "idle" && (
          <>
            <p className="text-center text-gray-600 text-sm max-w-sm">
              Tap below to open the camera and photograph the triage card.
            </p>
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="sr-only"
              aria-hidden
              onChange={onFileChange}
            />
            <button
              type="button"
              onClick={openCamera}
              className="w-full max-w-sm min-h-[52px] rounded-2xl bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white text-base font-semibold shadow-lg shadow-primary-600/25 transition-colors"
            >
              Take photo
            </button>
          </>
        )}

        {phase === "uploading" && (
          <div className="flex flex-col items-center gap-4">
            <div
              className="h-10 w-10 rounded-full border-2 border-primary-200 border-t-primary-600 animate-spin"
              aria-hidden
            />
            <p className="text-primary-800 text-sm">Uploading…</p>
          </div>
        )}

        {phase === "success" && (
          <div className="w-full max-w-sm flex flex-col items-stretch gap-6">
            <p className="text-center text-lg font-medium text-primary-700">
              Photo uploaded successfully
            </p>
            <button
              type="button"
              onClick={nextPatient}
              className="w-full min-h-[52px] rounded-2xl border-2 border-primary-300 bg-white hover:bg-primary-50 active:bg-primary-100 text-primary-900 text-base font-semibold transition-colors shadow-sm"
            >
              Next patient
            </button>
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="w-full max-w-sm rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 text-center"
          >
            {error}
          </div>
        )}
      </main>
    </div>
  );
}

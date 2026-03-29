import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import App from "./App";
import HospitalDashboard from "./components/HospitalDashboard";
import Login from "./components/Login";
import TriagePage from "./components/TriagePage";
import { HospitalAccessGate, ProtectedRoute } from "./components/ProtectedRoute";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/triage"
            element={
              <ProtectedRoute triagerOnly>
                <TriagePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute adminOnly>
                <App />
              </ProtectedRoute>
            }
          />
          <Route
            path="/hospital/:hospitalId"
            element={
              <ProtectedRoute>
                <HospitalAccessGate>
                  <HospitalDashboard />
                </HospitalAccessGate>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);

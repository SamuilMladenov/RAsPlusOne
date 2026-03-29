import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import * as api from "../api";
import BrandLogo from "./BrandLogo";

export default function Login() {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname;

  useEffect(() => {
    if (!isAuthenticated || !user) return;
    if (user.role === "triager") {
      navigate("/triage", { replace: true });
    } else if (user.role === "hospital" && user.hospitalId) {
      navigate(`/hospital/${user.hospitalId}`, { replace: true });
    } else {
      navigate(from && from !== "/login" ? from : "/", { replace: true });
    }
  }, [isAuthenticated, user, navigate, from]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.login(email.trim(), password);
      login(data);
      if (data.role === "triager") {
        navigate("/triage", { replace: true });
      } else if (data.role === "hospital" && data.hospital_id) {
        navigate(`/hospital/${data.hospital_id}`, { replace: true });
      } else {
        navigate(from && from !== "/login" ? from : "/", { replace: true });
      }
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-xl border border-primary-100 p-8">
        <div className="text-center mb-8 space-y-3">
          <div className="flex justify-center">
            <BrandLogo size="large" className="mx-auto" />
          </div>
          <p className="text-sm text-gray-500">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
              {error}
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-primary-800 mb-1">
              Email
            </label>
            <input
              type="email"
              autoComplete="username"
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-400 focus:border-primary-500 outline-none transition-shadow"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-primary-800 mb-1">
              Password
            </label>
            <input
              type="password"
              autoComplete="current-password"
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-400 focus:border-primary-500 outline-none transition-shadow"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors disabled:opacity-50 shadow-sm"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

import { Navigate, useLocation, useParams } from "react-router-dom";
import { useAuth } from "../AuthContext";

/** Requires login. If adminOnly, sends hospital users to their dashboard. If triagerOnly, only triagers may access. */
export function ProtectedRoute({ children, adminOnly, triagerOnly }) {
  const { token, user } = useAuth();
  const location = useLocation();

  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (triagerOnly && user.role !== "triager") {
    if (user.role === "admin") {
      return <Navigate to="/" replace />;
    }
    if (user.role === "hospital" && user.hospitalId) {
      return <Navigate to={`/hospital/${user.hospitalId}`} replace />;
    }
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user.role !== "admin") {
    if (user.role === "triager") {
      return <Navigate to="/triage" replace />;
    }
    return (
      <Navigate
        to={user.hospitalId ? `/hospital/${user.hospitalId}` : "/login"}
        replace
      />
    );
  }

  return children;
}

/** Ensures hospital-role users only open their own hospital page. */
export function HospitalAccessGate({ children }) {
  const { hospitalId } = useParams();
  const { user } = useAuth();

  if (user?.role === "triager") {
    return <Navigate to="/triage" replace />;
  }

  if (user?.role === "hospital" && user.hospitalId && user.hospitalId !== hospitalId) {
    return <Navigate to={`/hospital/${user.hospitalId}`} replace />;
  }

  return children;
}

import { Navigate, useLocation, useParams } from "react-router-dom";
import { useAuth } from "../AuthContext";

/** Requires login. If adminOnly, sends hospital users to their dashboard. */
export function ProtectedRoute({ children, adminOnly }) {
  const { token, user } = useAuth();
  const location = useLocation();

  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (adminOnly && user.role !== "admin") {
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

  if (user?.role === "hospital" && user.hospitalId && user.hospitalId !== hospitalId) {
    return <Navigate to={`/hospital/${user.hospitalId}`} replace />;
  }

  return children;
}

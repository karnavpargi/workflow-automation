import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth, type Role } from "./AuthProvider";

export interface RoleGuardProps {
  allow: Role[];
  children: ReactNode;
  fallback?: string;
}

export function RoleGuard({ allow, children, fallback = "/login" }: RoleGuardProps) {
  const { user } = useAuth();
  if (!user) return <Navigate to={fallback} replace />;
  if (!allow.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

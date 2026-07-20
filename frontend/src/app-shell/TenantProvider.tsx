import { useEffect, type ReactNode } from "react";
import { useAuth } from "./AuthProvider";

/**
 * Wrapper component that keeps ``AuthProvider.tenantSlug`` in sync with
 * a chosen source (subdomain today, a tenant-selector in a follow-up).
 *
 * Currently a passthrough that restores the last-used tenant from
 * localStorage; the subdomain parser is added when deploy topology
 * requires it.
 */
export function TenantProvider({ children }: { children: ReactNode }) {
  const { tenantSlug, setTenantSlug } = useAuth();
  useEffect(() => {
    if (!tenantSlug) {
      const stored = window.localStorage.getItem("wa.tenant.v1");
      if (stored) setTenantSlug(stored);
    } else {
      window.localStorage.setItem("wa.tenant.v1", tenantSlug);
    }
  }, [tenantSlug, setTenantSlug]);
  return <>{children}</>;
}

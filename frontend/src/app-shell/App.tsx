import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { RoleGuard } from "./RoleGuard";
import { Dashboard } from "../admin-portal/Dashboard";
import { Clients } from "../admin-portal/Clients";
import { Invoices } from "../admin-portal/Invoices";
import { Followups } from "../admin-portal/Followups";
import { DataEntry } from "../admin-portal/DataEntry";
import { AuditLog } from "../admin-portal/AuditLog";
import { DraftReview } from "../admin-portal/DraftReview";
import { OnboardingStatus } from "../client-portal/Status";
import { ClientInvoices } from "../client-portal/Invoices";
import { Login } from "./Login";

export function App() {
  const { user, logout, tenantSlug, setTenantSlug } = useAuth();

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app">
      <header className="app__header">
        <strong>Workflow Automation</strong>
        <span className="app__tenant">
          Tenant:
          <input
            aria-label="Tenant slug"
            value={tenantSlug ?? ""}
            onChange={(e) => setTenantSlug(e.target.value)}
            placeholder="acme"
          />
        </span>
        <span className="app__user">{user.email} ({user.role})</span>
        <button onClick={logout}>Sign out</button>
      </header>
      <nav className="app__nav">
        {user.role === "client" ? (
          <>
            <Link to="/onboarding">Onboarding</Link>
            <Link to="/invoices">Invoices</Link>
          </>
        ) : (
          <>
            <Link to="/">Dashboard</Link>
            <Link to="/clients">Clients</Link>
            <Link to="/invoices">Invoices</Link>
            <Link to="/followups">Follow-ups</Link>
            <Link to="/data-entry">Data entry</Link>
            <Link to="/drafts">Drafts</Link>
            <Link to="/audit">Audit</Link>
          </>
        )}
      </nav>
      <main className="app__main">
        <Routes>
          {user.role === "client" ? (
            <>
              <Route path="/onboarding" element={<OnboardingStatus />} />
              <Route path="/invoices" element={<ClientInvoices />} />
              <Route path="*" element={<Navigate to="/onboarding" replace />} />
            </>
          ) : (
            <>
              <Route
                path="/"
                element={
                  <RoleGuard allow={["admin", "member"]}>
                    <Dashboard />
                  </RoleGuard>
                }
              />
              <Route
                path="/clients"
                element={
                  <RoleGuard allow={["admin", "member"]}>
                    <Clients />
                  </RoleGuard>
                }
              />
              <Route
                path="/invoices"
                element={
                  <RoleGuard allow={["admin", "member"]}>
                    <Invoices />
                  </RoleGuard>
                }
              />
              <Route
                path="/followups"
                element={
                  <RoleGuard allow={["admin", "member"]}>
                    <Followups />
                  </RoleGuard>
                }
              />
              <Route
                path="/data-entry"
                element={
                  <RoleGuard allow={["admin", "member"]}>
                    <DataEntry />
                  </RoleGuard>
                }
              />
              <Route
                path="/drafts"
                element={
                  <RoleGuard allow={["admin"]}>
                    <DraftReview />
                  </RoleGuard>
                }
              />
              <Route
                path="/audit"
                element={
                  <RoleGuard allow={["admin"]}>
                    <AuditLog />
                  </RoleGuard>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </>
          )}
        </Routes>
      </main>
    </div>
  );
}

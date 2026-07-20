import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../app-shell/AuthProvider";
import { RoleGuard } from "../app-shell/RoleGuard";

function Probe() {
  return <div>secret</div>;
}

describe("RoleGuard", () => {
  it("redirects to /login when no user is authenticated", () => {
    // localStorage is empty by default in jsdom.
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route path="/login" element={<div>login page</div>} />
            <Route
              path="/secret"
              element={
                <RoleGuard allow={["admin"]}>
                  <Probe />
                </RoleGuard>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.queryByText("secret")).not.toBeInTheDocument();
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("renders the children when the role is allowed", () => {
    const storage: Record<string, string> = {
      "wa.auth.v1": JSON.stringify({
        accessToken: "t",
        user: { id: 1, email: "a@x.io", role: "admin" },
        tenantSlug: "acme",
      }),
    };
    vi.stubGlobal(
      "localStorage",
      {
        getItem: (k: string) => storage[k] ?? null,
        setItem: (k: string, v: string) => {
          storage[k] = v;
        },
        removeItem: (k: string) => {
          delete storage[k];
        },
      }
    );
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route
              path="/secret"
              element={
                <RoleGuard allow={["admin"]}>
                  <Probe />
                </RoleGuard>
              }
            />
            <Route path="/" element={<div>home</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.getByText("secret")).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

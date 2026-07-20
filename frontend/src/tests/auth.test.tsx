import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "../app-shell/AuthProvider";

function Probe() {
  const { user, login, logout, tenantSlug, setTenantSlug } = useAuth();
  return (
    <div>
      <span data-testid="user">{user ? user.email : "none"}</span>
      <span data-testid="role">{user ? user.role : "none"}</span>
      <span data-testid="tenant">{tenantSlug ?? "none"}</span>
      <button onClick={() => login("a@x.io", "p")}>login</button>
      <button onClick={logout}>logout</button>
      <button onClick={() => setTenantSlug("acme")}>set</button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("starts unauthenticated", () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(screen.getByTestId("role")).toHaveTextContent("none");
  });

  it("logs in, sets the user, and persists across remounts", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => ({
        access: "tok-1",
        user: { id: 1, email: "a@x.io", role: "admin" },
      }),
      text: async () => "",
    }));
    vi.stubGlobal("fetch", fetchMock);

    const { unmount } = render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await userEvent.click(screen.getByText("login"));
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("a@x.io")
    );
    expect(screen.getByTestId("role")).toHaveTextContent("admin");

    unmount();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    expect(screen.getByTestId("user")).toHaveTextContent("a@x.io");
    vi.unstubAllGlobals();
  });

  it("logs out and clears the user", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        status: 200,
        headers: { get: () => "application/json" },
        json: async () => ({
          access: "tok-1",
          user: { id: 1, email: "a@x.io", role: "admin" },
        }),
        text: async () => "",
      }))
    );
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await userEvent.click(screen.getByText("login"));
    await waitFor(() => screen.getByTestId("user").textContent === "a@x.io");
    await userEvent.click(screen.getByText("logout"));
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    vi.unstubAllGlobals();
  });

  it("stores and restores the tenant slug", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await userEvent.click(screen.getByText("set"));
    expect(screen.getByTestId("tenant")).toHaveTextContent("acme");
  });
});

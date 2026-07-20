import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../app-shell/AuthProvider";
import { Clients } from "../admin-portal/Clients";

function wrap(node: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>{node}</AuthProvider>
    </QueryClientProvider>
  );
}

describe("Clients page", () => {
  it("renders the create form", () => {
    render(wrap(<Clients />));
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create/i })).toBeInTheDocument();
  });

  it("submits the form and calls the API", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith("/api/clients/") && init?.method !== "POST") {
        return {
          ok: true,
          status: 200,
          headers: { get: () => "application/json" },
          json: async () => [{ id: 1, name: "Acme", email: "a@x.io" }],
          text: async () => "",
        };
      }
      if (url.endsWith("/api/clients/") && init?.method === "POST") {
        return {
          ok: true,
          status: 201,
          headers: { get: () => "application/json" },
          json: async () => ({ id: 2, name: "Acme", email: "a@x.io" }),
          text: async () => "",
        };
      }
      return {
        ok: true,
        status: 200,
        headers: { get: () => "application/json" },
        json: async () => [],
        text: async () => "",
      };
    });
    vi.stubGlobal("fetch", fetchMock);
    render(wrap(<Clients />));
    await userEvent.type(screen.getByLabelText("Name"), "Acme");
    await userEvent.type(screen.getByLabelText("Email"), "a@x.io");
    await userEvent.click(screen.getByRole("button", { name: /create/i }));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    vi.unstubAllGlobals();
  });
});

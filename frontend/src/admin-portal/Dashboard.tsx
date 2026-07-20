import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../app-shell/AuthProvider";
import { Table, type Column } from "../ui-kit";

interface Counts {
  clients: number;
  open_invoices: number;
  due_followups: number;
}

export function Dashboard() {
  const { api } = useAuth();
  const { data, isLoading, error } = useQuery<Counts>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<Counts>("/api/dashboard/"),
  });
  const columns: Column<[string, number]>[] = [
    { key: "label", header: "Metric", render: (r) => r[0] },
    { key: "value", header: "Count", render: (r) => r[1] },
  ];
  const rows: [string, number][] = [
    ["Clients", data?.clients ?? 0],
    ["Open invoices", data?.open_invoices ?? 0],
    ["Due follow-ups", data?.due_followups ?? 0],
  ];
  return (
    <section>
      <h1>Dashboard</h1>
      {isLoading && <p>Loading…</p>}
      {error && <p role="alert">Failed to load dashboard.</p>}
      <Table columns={columns} rows={rows} rowKey={(r) => r[0]} />
    </section>
  );
}

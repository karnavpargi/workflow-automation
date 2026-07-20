import { useQuery } from "@tanstack/react-query";
import { Table, type Column } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface AuditEntry {
  id: number;
  event: string;
  actor: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}

export function AuditLog() {
  const { api } = useAuth();
  const { data: entries = [] } = useQuery<AuditEntry[]>({
    queryKey: ["audit"],
    queryFn: () => api.get<AuditEntry[]>("/api/audit-log/"),
    enabled: false, // not yet shipped; keeps the page a stub until wired
  });
  const columns: Column<AuditEntry>[] = [
    { key: "event", header: "Event", render: (r) => r.event },
    { key: "actor", header: "Actor", render: (r) => r.actor ?? "—" },
    { key: "at", header: "When", render: (r) => r.created_at },
  ];
  return (
    <section>
      <h1>Audit log</h1>
      <Table columns={columns} rows={entries} rowKey={(r) => String(r.id)} emptyMessage="No entries yet" />
    </section>
  );
}

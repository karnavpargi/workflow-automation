import { useQuery } from "@tanstack/react-query";
import { Table, type Column } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface Onboarding {
  id: number;
  template: string;
  status: string;
  started_at: string;
}

export function OnboardingStatus() {
  const { api } = useAuth();
  const { data: runs = [] } = useQuery<Onboarding[]>({
    queryKey: ["my-onboarding"],
    queryFn: () => api.get<Onboarding[]>("/api/onboarding/runs/"),
    enabled: false, // until the per-user runs endpoint ships
  });
  const columns: Column<Onboarding>[] = [
    { key: "template", header: "Template", render: (r) => r.template },
    { key: "status", header: "Status", render: (r) => r.status },
    { key: "started", header: "Started", render: (r) => r.started_at },
  ];
  return (
    <section>
      <h1>Onboarding</h1>
      <Table columns={columns} rows={runs} rowKey={(r) => String(r.id)} emptyMessage="No onboarding in progress" />
    </section>
  );
}

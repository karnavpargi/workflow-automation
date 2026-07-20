import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Table, type Column, toast } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface Reminder {
  id: number;
  subject: string;
  due_at: string;
  status: string;
}

export function Followups() {
  const { api } = useAuth();
  const qc = useQueryClient();
  const { data: reminders = [] } = useQuery<Reminder[]>({
    queryKey: ["reminders"],
    queryFn: () => api.get<Reminder[]>("/api/reminders/"),
  });
  const cancel = useMutation({
    mutationFn: (id: number) => api.post<Reminder>(`/api/reminders/${id}/cancel/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reminders"] });
      toast("Reminder cancelled", "success");
    },
    onError: (e) => toast(e instanceof Error ? e.message : "Cancel failed", "danger"),
  });
  const columns: Column<Reminder>[] = [
    { key: "subject", header: "Subject", render: (r) => r.subject },
    { key: "due", header: "Due", render: (r) => r.due_at },
    { key: "status", header: "Status", render: (r) => r.status },
    {
      key: "actions",
      header: "",
      render: (r) =>
        r.status !== "cancelled" ? (
          <Button variant="danger" onClick={() => cancel.mutate(r.id)}>
            Cancel
          </Button>
        ) : null,
    },
  ];
  return (
    <section>
      <h1>Follow-ups</h1>
      <Table columns={columns} rows={reminders} rowKey={(r) => String(r.id)} />
    </section>
  );
}

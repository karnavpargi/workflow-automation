import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Table, type Column, toast } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface Draft {
  id: number;
  subject: string;
  draft_text: string;
  status: string;
}

export function DraftReview() {
  const { api } = useAuth();
  const qc = useQueryClient();
  const { data: drafts = [] } = useQuery<Draft[]>({
    queryKey: ["drafts"],
    queryFn: () => api.get<Draft[]>("/api/reminders/?status=draft"),
  });
  const approve = useMutation({
    mutationFn: (id: number) => api.post<Draft>(`/api/reminders/${id}/approve/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["drafts"] });
      toast("Draft approved", "success");
    },
    onError: (e) => toast(e instanceof Error ? e.message : "Approve failed", "danger"),
  });
  const columns: Column<Draft>[] = [
    { key: "subject", header: "Subject", render: (r) => r.subject },
    { key: "text", header: "Draft", render: (r) => r.draft_text },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <Button variant="primary" onClick={() => approve.mutate(r.id)}>
          Approve
        </Button>
      ),
    },
  ];
  return (
    <section>
      <h1>Drafts (HITL)</h1>
      <Table columns={columns} rows={drafts} rowKey={(r) => String(r.id)} emptyMessage="No drafts awaiting review" />
    </section>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Table, type Column, toast } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface Invoice {
  id: number;
  number: string;
  status: string;
  total: string;
  due_date: string;
}

export function Invoices() {
  const { api } = useAuth();
  const qc = useQueryClient();
  const { data: invoices = [] } = useQuery<Invoice[]>({
    queryKey: ["invoices"],
    queryFn: () => api.get<Invoice[]>("/api/invoices/"),
  });
  const issue = useMutation({
    mutationFn: (id: number) => api.post<Invoice>(`/api/invoices/${id}/issue/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      toast("Invoice issued", "success");
    },
    onError: (e) => toast(e instanceof Error ? e.message : "Issue failed", "danger"),
  });
  const columns: Column<Invoice>[] = [
    { key: "number", header: "Number", render: (r) => r.number },
    { key: "status", header: "Status", render: (r) => r.status },
    { key: "total", header: "Total", render: (r) => r.total },
    { key: "due", header: "Due", render: (r) => r.due_date },
    {
      key: "actions",
      header: "",
      render: (r) =>
        r.status === "draft" ? (
          <Button variant="secondary" onClick={() => issue.mutate(r.id)}>
            Issue
          </Button>
        ) : null,
    },
  ];
  return (
    <section>
      <h1>Invoices</h1>
      <Table columns={columns} rows={invoices} rowKey={(r) => String(r.id)} />
    </section>
  );
}

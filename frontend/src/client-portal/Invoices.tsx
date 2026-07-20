import { useQuery } from "@tanstack/react-query";
import { Table, type Column } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface ClientInvoice {
  id: number;
  number: string;
  status: string;
  total: string;
  due_date: string;
}

export function ClientInvoices() {
  const { api } = useAuth();
  const { data: invoices = [] } = useQuery<ClientInvoice[]>({
    queryKey: ["my-invoices"],
    queryFn: () => api.get<ClientInvoice[]>("/api/invoices/"),
  });
  const columns: Column<ClientInvoice>[] = [
    { key: "number", header: "Number", render: (r) => r.number },
    { key: "status", header: "Status", render: (r) => r.status },
    { key: "total", header: "Total", render: (r) => r.total },
    { key: "due", header: "Due", render: (r) => r.due_date },
    {
      key: "pdf",
      header: "PDF",
      render: (r) => <a href={`/api/invoices/${r.id}/pdf_url/`} target="_blank" rel="noreferrer">Download</a>,
    },
  ];
  return (
    <section>
      <h1>My invoices</h1>
      <Table columns={columns} rows={invoices} rowKey={(r) => String(r.id)} emptyMessage="No invoices yet" />
    </section>
  );
}

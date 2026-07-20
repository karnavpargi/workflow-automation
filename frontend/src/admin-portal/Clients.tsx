import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Input, Table, type Column, toast } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

interface Client {
  id: number;
  name: string;
  email: string;
}

export function Clients() {
  const { api } = useAuth();
  const qc = useQueryClient();
  const { data: clients = [] } = useQuery<Client[]>({
    queryKey: ["clients"],
    queryFn: () => api.get<Client[]>("/api/clients/"),
  });
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const create = useMutation({
    mutationFn: () => api.post<Client>("/api/clients/", { name, email }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      setName("");
      setEmail("");
      toast("Client created", "success");
    },
    onError: (e) => toast(e instanceof Error ? e.message : "Create failed", "danger"),
  });
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }
  const columns: Column<Client>[] = [
    { key: "name", header: "Name", render: (r) => r.name },
    { key: "email", header: "Email", render: (r) => r.email },
  ];
  return (
    <section>
      <h1>Clients</h1>
      <form onSubmit={onSubmit} aria-label="Create client">
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </form>
      <Table columns={columns} rows={clients} rowKey={(r) => String(r.id)} />
    </section>
  );
}

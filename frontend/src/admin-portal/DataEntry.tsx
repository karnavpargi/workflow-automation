import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, toast } from "../ui-kit";
import { useAuth } from "../app-shell/AuthProvider";

export function DataEntry() {
  const { api } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Pick a CSV first");
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/dataentry/csv/", {
        method: "POST",
        body: fd,
        credentials: "include",
        headers: {
          "X-Tenant-Slug": api["getTenantSlug"]() ?? "",
          Authorization: `Bearer ${api["getAccessToken"]() ?? ""}`,
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    },
    onSuccess: (data) => toast(`Uploaded ${data.count} rows`, "success"),
    onError: (e) => toast(e instanceof Error ? e.message : "Upload failed", "danger"),
  });
  return (
    <section>
      <h1>Data entry</h1>
      <p>Upload a CSV (header row + data rows).</p>
      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        aria-label="CSV file"
      />
      <Button onClick={() => upload.mutate()} disabled={!file || upload.isPending}>
        {upload.isPending ? "Uploading…" : "Upload"}
      </Button>
    </section>
  );
}

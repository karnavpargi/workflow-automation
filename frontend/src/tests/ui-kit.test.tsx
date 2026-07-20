import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button, Input, Modal, Table, toast } from "../ui-kit";

describe("Button", () => {
  it("renders children and is clickable", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save</Button>);
    const btn = screen.getByRole("button", { name: "Save" });
    await userEvent.click(btn);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled when the disabled prop is set", () => {
    render(<Button disabled>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});

describe("Input", () => {
  it("renders the label and associates it with the input", () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
  });

  it("reports an error via aria-invalid + role=alert", () => {
    render(<Input label="Email" error="required" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("required");
  });
});

describe("Table", () => {
  type Row = { id: string; name: string };
  const columns = [
    { key: "id", header: "ID", render: (r: Row) => r.id },
    { key: "name", header: "Name", render: (r: Row) => r.name },
  ];

  it("renders a row per data item", () => {
    const rows: Row[] = [
      { id: "1", name: "Alice" },
      { id: "2", name: "Bob" },
    ];
    render(
      <Table columns={columns} rows={rows} rowKey={(r) => r.id} />
    );
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("shows an empty message when no rows", () => {
    render(
      <Table columns={columns} rows={[]} rowKey={(r) => r.id} />
    );
    expect(screen.getByText("No rows")).toBeInTheDocument();
  });
});

describe("Modal", () => {
  it("renders nothing when closed", () => {
    render(
      <Modal open={false} onClose={() => {}} title="Hi">
        <p>content</p>
      </Modal>
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders a dialog with the title and content when open", () => {
    render(
      <Modal open={true} onClose={() => {}} title="Confirm">
        <p>Are you sure?</p>
      </Modal>
    );
    const dlg = screen.getByRole("dialog");
    expect(dlg).toHaveAttribute("aria-modal", "true");
    expect(dlg).toHaveTextContent("Confirm");
    expect(dlg).toHaveTextContent("Are you sure?");
  });
});

describe("toast", () => {
  it("dispatches a window event when called", () => {
    const onToast = vi.fn();
    window.addEventListener("wa:toast", onToast as EventListener);
    toast("Saved", "success");
    expect(onToast).toHaveBeenCalledOnce();
    window.removeEventListener("wa:toast", onToast as EventListener);
  });
});

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Input, toast } from "../ui-kit";
import { useAuth } from "./AuthProvider";

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(email, password);
      toast("Welcome back", "success");
      nav("/", { replace: true });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Login failed";
      setErr(msg);
      toast(msg, "danger");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login">
      <form onSubmit={onSubmit} aria-labelledby="login-title">
        <h1 id="login-title">Sign in</h1>
        <Input
          label="Email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={err ?? undefined}
          required
        />
        <Button type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </main>
  );
}

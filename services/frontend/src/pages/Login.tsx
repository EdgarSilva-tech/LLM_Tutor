import { useState } from "react";
import { useAuth } from "../auth";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const nav = useNavigate();
  const { login } = useAuth();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await login(username, password);
      nav("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? "Falha no login");
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ padding: 16, display: "grid", gap: 8 }}>
      <h2>Entrar</h2>
      <input placeholder="username" value={username} onChange={(e) => setU(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={(e) => setP(e.target.value)} />
      <button type="submit">Entrar</button>
      {err && <div style={{ color: "red" }}>{err}</div>}
    </form>
  );
}



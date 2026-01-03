import { useState } from "react";
import { api } from "../api";

export default function Rag() {
  const [q, setQ] = useState("");
  const [ans, setAns] = useState<string>("");
  const [ctx, setCtx] = useState<string[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function ask() {
    setErr(null);
    setAns("");
    setCtx(null);
    try {
      const { data } = await api.post("/rag/question-answer", {
        question: q,
        top_k: 3,
      });
      setAns(data?.answer ?? JSON.stringify(data));
      if (Array.isArray(data?.context)) setCtx(data.context);
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? e?.message ?? "Erro no pedido");
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>RAG</h2>
      <textarea rows={4} style={{ width: 480 }} value={q} onChange={(e) => setQ(e.target.value)} />
      <div>
        <button onClick={ask}>Perguntar</button>
      </div>
      {err && <div style={{ color: "red", marginTop: 8 }}>{err}</div>}
      {ans && (
        <pre style={{ background: "#f7f7f7", padding: 12, marginTop: 12, whiteSpace: "pre-wrap" }}>
          {ans}
        </pre>
      )}
      {ctx && ctx.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4>Contexto</h4>
          <ul>
            {ctx.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}



import { useEffect, useState } from "react";
import { api } from "../api";

export default function EvalStatus() {
  const [job, setJob] = useState("");
  const [status, setStatus] = useState<any>(null);
  const [poll, setPoll] = useState<boolean>(false);

  async function fetchStatus(id: string) {
    if (!id) return;
    // ajuste o caminho se o serviço expuser outro prefixo
    const { data } = await api.get(`/evaluation/eval-service/jobs/${id}`);
    setStatus(data);
  }

  useEffect(() => {
    if (!poll || !job) return;
    const h = setInterval(() => fetchStatus(job), 2000);
    return () => clearInterval(h);
  }, [poll, job]);

  return (
    <div style={{ padding: 16 }}>
      <h2>Status do Job de Avaliação</h2>
      <input placeholder="job_id" value={job} onChange={(e) => setJob(e.target.value)} />
      <button onClick={() => fetchStatus(job)}>Consultar</button>
      <label style={{ marginLeft: 12 }}>
        <input type="checkbox" checked={poll} onChange={(e) => setPoll(e.target.checked)} /> Polling
      </label>
      {status && (
        <pre style={{ background: "#f7f7f7", padding: 12, marginTop: 12 }}>
          {JSON.stringify(status, null, 2)}
        </pre>
      )}
    </div>
  );
}



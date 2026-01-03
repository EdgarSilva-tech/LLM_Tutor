import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { api } from "../api";
export default function EvalStatus() {
    const [job, setJob] = useState("");
    const [status, setStatus] = useState(null);
    const [poll, setPoll] = useState(false);
    async function fetchStatus(id) {
        if (!id)
            return;
        // ajuste o caminho se o serviço expuser outro prefixo
        const { data } = await api.get(`/evaluation/eval-service/jobs/${id}`);
        setStatus(data);
    }
    useEffect(() => {
        if (!poll || !job)
            return;
        const h = setInterval(() => fetchStatus(job), 2000);
        return () => clearInterval(h);
    }, [poll, job]);
    return (_jsxs("div", { style: { padding: 16 }, children: [_jsx("h2", { children: "Status do Job de Avalia\u00E7\u00E3o" }), _jsx("input", { placeholder: "job_id", value: job, onChange: (e) => setJob(e.target.value) }), _jsx("button", { onClick: () => fetchStatus(job), children: "Consultar" }), _jsxs("label", { style: { marginLeft: 12 }, children: [_jsx("input", { type: "checkbox", checked: poll, onChange: (e) => setPoll(e.target.checked) }), " Polling"] }), status && (_jsx("pre", { style: { background: "#f7f7f7", padding: 12, marginTop: 12 }, children: JSON.stringify(status, null, 2) }))] }));
}

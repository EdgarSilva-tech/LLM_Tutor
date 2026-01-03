import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { api } from "../api";
export default function Rag() {
    const [q, setQ] = useState("");
    const [ans, setAns] = useState("");
    async function ask() {
        const { data } = await api.post("/rag/ask", { question: q });
        setAns(data?.answer ?? JSON.stringify(data));
    }
    return (_jsxs("div", { style: { padding: 16 }, children: [_jsx("h2", { children: "RAG" }), _jsx("textarea", { rows: 4, style: { width: 480 }, value: q, onChange: (e) => setQ(e.target.value) }), _jsx("div", { children: _jsx("button", { onClick: ask, children: "Perguntar" }) }), ans && (_jsx("pre", { style: { background: "#f7f7f7", padding: 12, marginTop: 12, whiteSpace: "pre-wrap" }, children: ans }))] }));
}

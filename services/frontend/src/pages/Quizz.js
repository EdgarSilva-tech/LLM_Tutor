import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { api } from "../api";
export default function Quizz() {
    const [answers, setA] = useState("[]");
    const [job, setJob] = useState("");
    async function submit() {
        const body = { answers: JSON.parse(answers) };
        const { data } = await api.post("/quiz/generate-async", body, {
            headers: { "Content-Type": "application/json" }
        });
        setJob(data?.job_id ?? "");
    }
    return (_jsxs("div", { style: { padding: 16 }, children: [_jsx("h2", { children: "Quizz \u2192 Avalia\u00E7\u00E3o (ass\u00EDncrono)" }), _jsx("p", { children: "Insira respostas (JSON array), e submeta para gerar um job." }), _jsx("textarea", { rows: 6, style: { width: 480 }, value: answers, onChange: (e) => setA(e.target.value) }), _jsx("div", { children: _jsx("button", { onClick: submit, children: "Submeter" }) }), job && _jsxs("div", { children: ["Job ID: ", _jsx("code", { children: job })] })] }));
}

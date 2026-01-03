import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useAuth } from "../auth";
import { useNavigate } from "react-router-dom";
export default function Login() {
    const nav = useNavigate();
    const { login } = useAuth();
    const [username, setU] = useState("");
    const [password, setP] = useState("");
    const [err, setErr] = useState(null);
    async function onSubmit(e) {
        e.preventDefault();
        setErr(null);
        try {
            await login(username, password);
            nav("/");
        }
        catch (e) {
            setErr(e?.response?.data?.detail ?? "Falha no login");
        }
    }
    return (_jsxs("form", { onSubmit: onSubmit, style: { padding: 16, display: "grid", gap: 8 }, children: [_jsx("h2", { children: "Entrar" }), _jsx("input", { placeholder: "username", value: username, onChange: (e) => setU(e.target.value) }), _jsx("input", { placeholder: "password", type: "password", value: password, onChange: (e) => setP(e.target.value) }), _jsx("button", { type: "submit", children: "Entrar" }), err && _jsx("div", { style: { color: "red" }, children: err })] }));
}

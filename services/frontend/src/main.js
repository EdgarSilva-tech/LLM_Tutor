import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./auth";
import Login from "./pages/Login";
import Rag from "./pages/Rag";
import Quizz from "./pages/Quizz";
import EvalStatus from "./pages/EvalStatus";
const qc = new QueryClient();
function Nav() {
    const { token, logout } = useAuth();
    return (_jsxs("nav", { style: { display: "flex", gap: 12, padding: 12, borderBottom: "1px solid #ddd" }, children: [_jsx(Link, { to: "/", children: "RAG" }), _jsx(Link, { to: "/quizz", children: "Quizz" }), _jsx(Link, { to: "/status", children: "Eval Status" }), token ? _jsx("button", { onClick: logout, children: "Sair" }) : _jsx(Link, { to: "/login", children: "Entrar" })] }));
}
function RequireAuth({ children }) {
    const { token } = useAuth();
    if (!token)
        return _jsx(Navigate, { to: "/login", replace: true });
    return _jsx(_Fragment, { children: children });
}
function App() {
    return (_jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: _jsx(Login, {}) }), _jsx(Route, { path: "/", element: _jsx(RequireAuth, { children: _jsx(Rag, {}) }) }), _jsx(Route, { path: "/quizz", element: _jsx(RequireAuth, { children: _jsx(Quizz, {}) }) }), _jsx(Route, { path: "/status", element: _jsx(RequireAuth, { children: _jsx(EvalStatus, {}) }) })] }));
}
ReactDOM.createRoot(document.getElementById("root")).render(_jsx(React.StrictMode, { children: _jsx(QueryClientProvider, { client: qc, children: _jsx(AuthProvider, { children: _jsxs(BrowserRouter, { children: [_jsx(Nav, {}), _jsx(App, {})] }) }) }) }));

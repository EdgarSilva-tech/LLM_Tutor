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
  return (
    <nav style={{ display: "flex", gap: 12, padding: 12, borderBottom: "1px solid #ddd" }}>
      <Link to="/">RAG</Link>
      <Link to="/quizz">Quizz</Link>
      <Link to="/status">Eval Status</Link>
      {token ? <button onClick={logout}>Sair</button> : <Link to="/login">Entrar</Link>}
    </nav>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Rag />
          </RequireAuth>
        }
      />
      <Route
        path="/quizz"
        element={
          <RequireAuth>
            <Quizz />
          </RequireAuth>
        }
      />
      <Route
        path="/status"
        element={
          <RequireAuth>
            <EvalStatus />
          </RequireAuth>
        }
      />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <Nav />
          <App />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);



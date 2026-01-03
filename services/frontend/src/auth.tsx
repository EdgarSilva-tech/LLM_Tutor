import { createContext, useContext, useEffect, useState } from "react";
import { api, setAuthToken } from "./api";

type AuthCtx = {
  token?: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx>({} as AuthCtx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  useEffect(() => {
    setAuthToken(token || undefined);
  }, [token]);

  async function login(username: string, password: string) {
    const form = new URLSearchParams({ username, password });
    const { data } = await api.post("/auth/token", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setAuthToken(undefined);
  }

  return <Ctx.Provider value={{ token, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  return useContext(Ctx);
}



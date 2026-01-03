import { createContext, useContext, useEffect, useState } from "react";
import { jsx as _jsx } from "react/jsx-runtime";
import { api, setAuthToken } from "./api";
const Ctx = createContext({});
export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem("token"));
    useEffect(() => {
        setAuthToken(token || undefined);
    }, [token]);
    async function login(username, password) {
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
    return _jsx(Ctx.Provider, { value: { token, login, logout }, children: children });
}
export function useAuth() {
    return useContext(Ctx);
}

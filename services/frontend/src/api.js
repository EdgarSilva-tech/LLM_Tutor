import axios from "axios";
export const api = axios.create({
    baseURL: "/", // Ingress roteia por /auth /rag /quiz /evaluation
});
export function setAuthToken(token) {
    if (token)
        api.defaults.headers.common.Authorization = `Bearer ${token}`;
    else
        delete api.defaults.headers.common.Authorization;
}

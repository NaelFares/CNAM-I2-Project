import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  withCredentials: true,
  timeout: 20000,
});

export function extractApiError(err) {
  if (axios.isAxiosError(err) && err.response?.data) {
    const payload = err.response.data;
    return {
      code: payload.code ?? "API_ERROR",
      message: payload.message ?? "Une erreur est survenue.",
    };
  }
  return { code: "API_ERROR", message: "Une erreur est survenue." };
}

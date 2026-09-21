import axios from "axios";

// Exportee a part : les photos de profil sont servies par l'API sous un
// chemin absolu ("/media/..."), qu'il faut prefixer pour les afficher.
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 20000,
});

export function extractApiError(err) {
  if (axios.isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      return {
        code: "TIMEOUT",
        message: "Le traitement prend trop de temps. Reessayez dans quelques secondes.",
      };
    }

    if (err.response?.data) {
      const payload = err.response.data.detail ?? err.response.data;
      return {
        code: payload.code ?? "API_ERROR",
        message: payload.message ?? "Une erreur est survenue.",
      };
    }

    return {
      code: "API_ERROR",
      message: "Impossible de contacter le serveur.",
    };
  }
  return { code: "API_ERROR", message: "Une erreur est survenue." };
}

import { apiClient } from "./api";

export async function login(email, password) {
  return (await apiClient.post("/auth/login", { email, password })).data;
}

export async function register(payload) {
  return (await apiClient.post("/auth/register", payload)).data;
}

export async function logout() {
  await apiClient.post("/auth/logout");
}

export async function fetchSession() {
  return (await apiClient.get("/auth/session")).data;
}

export async function getProfile() {
  return (await apiClient.get("/profile")).data;
}

export async function updateProfile(payload) {
  return (await apiClient.put("/profile", payload)).data;
}

export async function searchAddress(query) {
  return (await apiClient.get("/geocode/search", { params: { q: query, limit: 5 } })).data;
}

export async function reverseAddress(lat, lon) {
  return (await apiClient.get("/geocode/reverse", { params: { lat, lon } })).data;
}

export async function previewSchedule(file) {
  const form = new FormData();
  form.append("file", file);
  return (
    await apiClient.post("/schedule/preview", form, {
      timeout: 180000,
    })
  ).data;
}

export async function confirmSchedule() {
  return (await apiClient.post("/schedule/confirm")).data;
}

export async function getScheduleEvents() {
  return (await apiClient.get("/schedule/events")).data;
}

export async function cancelPreview() {
  await apiClient.post("/schedule/cancel");
}

export async function generateRides() {
  return (await apiClient.post("/rides/generate")).data;
}

export async function findMatches() {
  return (await apiClient.post("/matches/find", null, { timeout: 45000 })).data;
}

export async function searchCarpoolMatches(payload) {
  return (await apiClient.post("/matches/search", payload, { timeout: 45000 })).data;
}

export async function getRoutePreview(params) {
  return (await apiClient.get("/routing/preview", { params })).data;
}

export async function dashboardSummary() {
  return (await apiClient.get("/dashboard/summary")).data;
}

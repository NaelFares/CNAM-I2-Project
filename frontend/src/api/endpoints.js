import { apiClient } from "./api";

const MATCHING_TIMEOUT_MS = 180000;

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

export async function uploadProfilePhoto(file) {
  const form = new FormData();
  form.append("file", file);
  // Content-Type volontairement non fixe : axios doit poser lui-meme la
  // frontiere multipart.
  return (await apiClient.post("/profile/photo", form, { timeout: 30000 })).data;
}

export async function deleteProfilePhoto() {
  return (await apiClient.delete("/profile/photo")).data;
}

export async function searchAddress(query) {
  return (await apiClient.get("/geocode/search", { params: { q: query, limit: 5 } })).data;
}

export async function reverseAddress(lat, lon) {
  return (await apiClient.get("/geocode/reverse", { params: { lat, lon } })).data;
}

export async function previewSchedule(file, privacyMode = false) {
  const form = new FormData();
  form.append("file", file);
  form.append("privacy_mode", String(privacyMode));
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

// --- Reservation (flux conducteur/passager) ---
export async function getMyRideSelections() {
  return (await apiClient.get("/rides/my-selections")).data;
}

export async function getMyRideOffers() {
  return (await apiClient.get("/rides/my-offers")).data;
}

// Proposer un trajet independamment de l'emploi du temps.
export async function createOffer(payload) {
  return (await apiClient.post("/rides/offers", payload)).data;
}

// Annuler un trajet propose (supprime s'il a ete cree a la main).
export async function withdrawOffer(rideId) {
  return (await apiClient.delete(`/rides/${rideId}/offer`)).data;
}

// Interrupteur "Je prends ma voiture" sur un de mes trajets.
export async function setRideOffer(rideId, isOffer) {
  return (await apiClient.put(`/rides/${rideId}/offer`, { is_offer: isOffer })).data;
}

// `stop` : correspondance choisie (prise en charge, depose, heure de
// passage, detour), enregistree avec la demande pour le conducteur.
export async function selectRide(rideId, stop = null) {
  return (await apiClient.post(`/rides/${rideId}/select`, stop || undefined)).data;
}

// force : accepter malgre l'avertissement de detour total trop long.
export async function decideRidePassenger(rideId, passengerId, decision, force = false) {
  const params = force ? { force: true } : undefined;
  return (await apiClient.post(`/rides/${rideId}/passengers/${passengerId}/${decision}`, null, { params })).data;
}

export async function cancelRideSelection(rideId) {
  return (await apiClient.delete(`/rides/${rideId}/select`)).data;
}

// --- Suivi de la course (une fois la reservation acceptee) ---
export async function fetchTrackings() {
  return (await apiClient.get("/tracking")).data;
}

export async function rateRide(selectionId, score, comment = "") {
  return (
    await apiClient.post(`/tracking/selections/${selectionId}/rating`, { score, comment })
  ).data;
}

export async function fetchMyRatings() {
  return (await apiClient.get("/ratings/me")).data;
}

export async function confirmTrackingStep(selectionId, step) {
  return (await apiClient.post(`/tracking/selections/${selectionId}/steps/${step}`)).data;
}

export async function findMatches(weekStart, ladiesOnly = false) {
  return (
    await apiClient.post(
      "/matches/find",
      { week_start: weekStart },
      { params: { ladies_only: ladiesOnly }, timeout: MATCHING_TIMEOUT_MS }
    )
  ).data;
}

export async function searchCarpoolMatches(payload) {
  return (await apiClient.post("/matches/search", payload, { timeout: MATCHING_TIMEOUT_MS })).data;
}

export async function getRoutePreview(params) {
  return (await apiClient.get("/routing/preview", { params })).data;
}

export async function dashboardSummary() {
  return (await apiClient.get("/dashboard/summary")).data;
}

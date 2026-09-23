import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import {
  cancelRideSelection,
  confirmSchedule,
  dashboardSummary,
  decideRidePassenger,
  findMatches,
  generateRides,
  getMyRideOffers,
  getMyRideSelections,
  getProfile,
  getScheduleEvents,
  previewSchedule,
  searchCarpoolMatches,
  selectRide,
  updateProfile,
} from "../api/endpoints";
import { useAuthStore } from "./auth";
import { useFeedbackStore } from "./feedback";

const PENDING_RIDE_STORAGE_KEY = "studride.pendingRide";

function loadPendingRide() {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(window.sessionStorage.getItem(PENDING_RIDE_STORAGE_KEY)) || null;
  } catch {
    return null;
  }
}

export const useAppStore = defineStore("app", {
  state: () => ({
    profile: null,
    previewEvents: [],
    events: [],
    rides: [],
    matches: [],
    searchResults: [],
    searchRouteGeometry: [],
    mySelections: [],
    driverOffers: [],
    pendingRide: loadPendingRide(),
    ridesViewLoading: false,
    selectionLoadingRideId: null,
    summary: null,
    loading: false,
    loadingLabel: "",
    loadingDetail: "",
    loadingStartedAt: null,
  }),
  actions: {
    prepareRideSelection(match) {
      this.pendingRide = match ? { ...match } : null;
      if (typeof window === "undefined") return;
      if (this.pendingRide) {
        window.sessionStorage.setItem(PENDING_RIDE_STORAGE_KEY, JSON.stringify(this.pendingRide));
      } else {
        window.sessionStorage.removeItem(PENDING_RIDE_STORAGE_KEY);
      }
    },
    clearPendingRide() {
      this.pendingRide = null;
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(PENDING_RIDE_STORAGE_KEY);
      }
    },
    startLoading(label, detail = "") {
      this.loading = true;
      this.loadingLabel = label;
      this.loadingDetail = detail;
      this.loadingStartedAt = Date.now();
    },
    stopLoading() {
      this.loading = false;
      this.loadingLabel = "";
      this.loadingDetail = "";
      this.loadingStartedAt = null;
    },
    async loadProfile() {
      try {
        this.profile = await getProfile();
      } catch {
        this.profile = null;
      }
    },
    async saveProfile(payload) {
      const feedback = useFeedbackStore();
      this.startLoading("Sauvegarde du profil...", "Mise a jour de vos informations.");
      try {
        this.profile = await updateProfile(payload);
        const auth = useAuthStore();
        auth.user = { ...(auth.user || {}), ...this.profile };
        feedback.showSuccess("Profil sauvegarde avec succes.");
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.stopLoading();
      }
    },
    async loadSummary() {
      try {
        this.summary = await dashboardSummary();
      } catch {
        this.summary = null;
      }
    },
    async loadScheduleEvents() {
      try {
        const data = await getScheduleEvents();
        this.events = data.events;
      } catch {
        this.events = [];
      }
    },
    async previewSchedule(file, privacyMode = false) {
      const feedback = useFeedbackStore();
      const detail = privacyMode
        ? "Privacy mode : le modele analyse uniquement les en-tetes."
        : "Le modele identifie les colonnes et horaires a partir d'un echantillon.";
      this.startLoading("Analyse du planning...", detail);
      try {
        const data = await previewSchedule(file, privacyMode);
        this.previewEvents = data.events;
        if (data.requires_user_review) {
          const score = typeof data.confidence_score === "number" ? ` (${Math.round(data.confidence_score * 100)}%)` : "";
          feedback.showInfo(`Verification recommandee: confiance IA faible${score}.`);
        } else {
          feedback.showSuccess(data.feedback.message);
        }
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.stopLoading();
      }
    },
    async confirmSchedule() {
      const feedback = useFeedbackStore();
      this.startLoading("Confirmation et enregistrement...", "Enregistrement des cours importes.");
      try {
        const data = await confirmSchedule();
        this.events = data.events;
        this.previewEvents = [];
        feedback.showSuccess(data.feedback.message);
      } catch (err) {
        feedback.showError(extractApiError(err).message);
      } finally {
        this.stopLoading();
      }
    },
    async generateRides() {
      const feedback = useFeedbackStore();
      this.startLoading("Generation des trajets...", "Calcul des trajets aller/retour campus.");
      try {
        const data = await generateRides();
        this.rides = data.rides;
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.stopLoading();
      }
    },
    async loadMySelections() {
      const feedback = useFeedbackStore();
      this.ridesViewLoading = true;
      try {
        const data = await getMyRideSelections();
        this.mySelections = data.rides || [];
        return true;
      } catch (err) {
        this.mySelections = [];
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.ridesViewLoading = false;
      }
    },
    async loadDriverOffers() {
      const feedback = useFeedbackStore();
      this.ridesViewLoading = true;
      try {
        const data = await getMyRideOffers();
        this.driverOffers = data.rides || [];
        return true;
      } catch (err) {
        this.driverOffers = [];
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.ridesViewLoading = false;
      }
    },
    async decidePassenger(rideId, passengerId, decision) {
      const feedback = useFeedbackStore();
      this.selectionLoadingRideId = rideId;
      try {
        const data = await decideRidePassenger(rideId, passengerId, decision);
        await this.loadDriverOffers();
        feedback.showSuccess(data.feedback?.message || "Demande traitée.");
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.selectionLoadingRideId = null;
      }
    },
    async selectRide(rideId) {
      const feedback = useFeedbackStore();
      if (!rideId) {
        feedback.showError("Ce trajet ne peut pas etre selectionne.");
        return false;
      }

      this.selectionLoadingRideId = rideId;
      try {
        const data = await selectRide(rideId);
        const reservedMinute = String(this.pendingRide?.ride_time || "").slice(0, 16).replace("T", " ");
        const stillAvailable = (match) =>
          String(match.ride_id) !== String(rideId)
          && (!reservedMinute || String(match.ride_time || "").slice(0, 16).replace("T", " ") !== reservedMinute);
        this.searchResults = this.searchResults.filter(stillAvailable);
        this.matches = this.matches.filter(stillAvailable);
        this.clearPendingRide();
        await this.loadMySelections();
        feedback.showSuccess(data.feedback?.message || "Trajet selectionne.");
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.selectionLoadingRideId = null;
      }
    },
    async cancelRideSelection(rideId) {
      const feedback = useFeedbackStore();
      this.selectionLoadingRideId = rideId;
      try {
        const data = await cancelRideSelection(rideId);
        this.mySelections = this.mySelections.filter((ride) => ride.ride_id !== rideId);
        feedback.showSuccess(data.feedback?.message || "Selection annulee.");
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.selectionLoadingRideId = null;
      }
    },
    async findMatches(weekStart) {
      const feedback = useFeedbackStore();
      this.startLoading("Recherche des correspondances...", "Comparaison des trajets disponibles.");
      try {
        const data = await findMatches(weekStart);
        this.matches = data.matches;
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.stopLoading();
      }
    },
    async searchCarpoolTrip(payload) {
      const feedback = useFeedbackStore();
      this.startLoading("Recherche de covoiturage...", "Comparaison avec les trajets disponibles.");
      try {
        const data = await searchCarpoolMatches({
          origin_lat: payload.originLat,
          origin_lon: payload.originLon,
          dest_lat: payload.destLat,
          dest_lon: payload.destLon,
          ride_time: payload.rideTime,
          ride_type: payload.rideType,
        });
        this.searchResults = data.matches;
        this.searchRouteGeometry = data.search_route_geometry;
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.stopLoading();
      }
    },
  },
});



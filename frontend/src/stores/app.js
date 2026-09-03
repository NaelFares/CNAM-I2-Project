import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import {
  confirmSchedule,
  dashboardSummary,
  findMatches,
  generateRides,
  getProfile,
  getScheduleEvents,
  previewSchedule,
  searchCarpoolMatches,
  updateProfile,
} from "../api/endpoints";
import { useFeedbackStore } from "./feedback";

export const useAppStore = defineStore("app", {
  state: () => ({
    profile: null,
    previewEvents: [],
    events: [],
    rides: [],
    matches: [],
    searchResults: [],
    searchRouteGeometry: [],
    summary: null,
    loading: false,
    loadingLabel: "",
    loadingDetail: "",
    loadingStartedAt: null,
  }),
  actions: {
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
    async findMatches() {
      const feedback = useFeedbackStore();
      this.startLoading("Recherche des correspondances...", "Comparaison des trajets disponibles.");
      try {
        const data = await findMatches();
        this.matches = data.matches;
        feedback.showSuccess(data.feedback.message);
      } catch (err) {
        feedback.showError(extractApiError(err).message);
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
      } catch (err) {
        feedback.showError(extractApiError(err).message);
      } finally {
        this.stopLoading();
      }
    },
  },
});



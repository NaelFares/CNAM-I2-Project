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
    summary: null,
    loading: false,
  }),
  actions: {
    async loadProfile() {
      try {
        this.profile = await getProfile();
      } catch {
        this.profile = null;
      }
    },
    async saveProfile(payload) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        this.profile = await updateProfile(payload);
        feedback.showSuccess("Profil sauvegarde avec succes.");
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.loading = false;
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
    async previewSchedule(file) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await previewSchedule(file);
        this.previewEvents = data.events;
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.loading = false;
      }
    },
    async confirmSchedule() {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await confirmSchedule();
        this.events = data.events;
        this.previewEvents = [];
        feedback.showSuccess(data.feedback.message);
      } catch (err) {
        feedback.showError(extractApiError(err).message);
      } finally {
        this.loading = false;
      }
    },
    async generateRides() {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await generateRides();
        this.rides = data.rides;
        feedback.showSuccess(data.feedback.message);
      } catch (err) {
        feedback.showError(extractApiError(err).message);
      } finally {
        this.loading = false;
      }
    },
    async findMatches() {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await findMatches();
        this.matches = data.matches;
        feedback.showSuccess(data.feedback.message);
      } catch (err) {
        feedback.showError(extractApiError(err).message);
      } finally {
        this.loading = false;
      }
    },
  },
});



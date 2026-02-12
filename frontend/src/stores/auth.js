import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import { fetchSession, login, logout, register } from "../api/endpoints";
import { useFeedbackStore } from "./feedback";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    initialized: false,
    isLoggedIn: false,
    user: null,
    pendingEmail: "",
    loading: false,
  }),
  actions: {
    async restoreSession() {
      try {
        const data = await fetchSession();
        this.isLoggedIn = data.authenticated;
        this.user = data.user;
      } finally {
        this.initialized = true;
      }
    },
    async loginWithEmail(email) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await login(email);
        if (data.status === "register_required") {
          this.pendingEmail = email;
          this.isLoggedIn = false;
          feedback.showSuccess(data.feedback.message);
          return { registerRequired: true };
        }
        this.user = data.user;
        this.isLoggedIn = true;
        this.pendingEmail = "";
        feedback.showSuccess("Connexion réussie.");
        return { registerRequired: false };
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return { registerRequired: false };
      } finally {
        this.loading = false;
      }
    },
    async registerUser(payload) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await register(payload);
        this.user = data.user;
        this.isLoggedIn = true;
        this.pendingEmail = "";
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      await logout();
      this.isLoggedIn = false;
      this.user = null;
      this.pendingEmail = "";
    },
  },
});



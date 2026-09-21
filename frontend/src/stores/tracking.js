import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import {
  cancelRideSelection,
  confirmTrackingStep,
  createRideSelection,
  fetchTrackings,
} from "../api/endpoints";
import { isFinished } from "../lib/tracking";
import { useFeedbackStore } from "./feedback";

export const useTrackingStore = defineStore("tracking", {
  state: () => ({
    trackings: [],
    loading: false,
    loaded: false,
  }),
  getters: {
    // Les courses en cours sont ce qui interesse l'utilisateur maintenant ;
    // l'historique reste consultable mais passe au second plan.
    active: (state) => state.trackings.filter((t) => !isFinished(t.status)),
    finished: (state) => state.trackings.filter((t) => isFinished(t.status)),
  },
  actions: {
    async load() {
      this.loading = true;
      try {
        const data = await fetchTrackings();
        this.trackings = data.trackings;
        this.loaded = true;
      } catch {
        this.trackings = [];
      } finally {
        this.loading = false;
      }
    },
    /** Remplace une entree par la version renvoyee par l'API. */
    _replace(tracking) {
      const index = this.trackings.findIndex((t) => t.id === tracking.id);
      if (index >= 0) {
        this.trackings.splice(index, 1, tracking);
      } else {
        this.trackings.unshift(tracking);
      }
    },
    async reserve(rideId) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await createRideSelection(rideId);
        this._replace(data.tracking);
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.loading = false;
      }
    },
    async confirm(selectionId, step) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await confirmTrackingStep(selectionId, step);
        this._replace(data.tracking);
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        // L'autre partie a pu annuler entre-temps : on resynchronise pour
        // ne pas laisser un bouton qui ne marchera plus jamais.
        await this.load();
        return false;
      } finally {
        this.loading = false;
      }
    },
    async cancel(selectionId) {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await cancelRideSelection(selectionId);
        this._replace(data.tracking);
        feedback.showSuccess(data.feedback.message);
        return true;
      } catch (err) {
        feedback.showError(extractApiError(err).message);
        return false;
      } finally {
        this.loading = false;
      }
    },
  },
});

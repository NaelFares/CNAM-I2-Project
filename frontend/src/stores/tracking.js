import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import { confirmTrackingStep, fetchMyRatings, fetchTrackings, rateRide } from "../api/endpoints";
import { isFinished } from "../lib/tracking";
import { useFeedbackStore } from "./feedback";

export const useTrackingStore = defineStore("tracking", {
  state: () => ({
    trackings: [],
    loading: false,
    loaded: false,
    // Reputation du compte courant, rechargee apres chaque note recue.
    myRatings: { summary: { average: null, count: 0, tier_key: "newcomer", tier_label: "Nouveau" }, ratings: [] },
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
    async loadMyRatings() {
      try {
        this.myRatings = await fetchMyRatings();
      } catch {
        // La reputation est un complement : son echec ne doit pas vider
        // l'ecran de suivi.
      }
    },
    async rate(selectionId, score, comment = "") {
      const feedback = useFeedbackStore();
      this.loading = true;
      try {
        const data = await rateRide(selectionId, score, comment);
        feedback.showSuccess(data.feedback.message);
        // La note est definitive : on resynchronise pour que le formulaire
        // laisse place a la note donnee.
        await this.load();
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
  },
});

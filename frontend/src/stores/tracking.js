import { defineStore } from "pinia";

import { extractApiError } from "../api/api";
import { confirmTrackingStep, fetchMyRatings, fetchTrackings, rateRide } from "../api/endpoints";
import { isFinished } from "../lib/tracking";
import { useFeedbackStore } from "./feedback";

function byRideTime(a, b) {
  return String(a.ride_time).localeCompare(String(b.ride_time));
}

// Vrai si la course a lieu un jour posterieur a aujourd'hui (heure locale).
function isAfterToday(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const endOfToday = new Date();
  endOfToday.setHours(23, 59, 59, 999);
  return date > endOfToday;
}

export const useTrackingStore = defineStore("tracking", {
  state: () => ({
    trackings: [],
    loading: false,
    loaded: false,
    // Reputation du compte courant, rechargee apres chaque note recue.
    // Structure alignee sur RatingSummaryDTO : un seul palier par profil.
    myRatings: {
      summary: {
        average: null,
        count: 0,
        tier: { rides_count: 0, tier_key: "beginner", tier_label: "Débutant", rides_to_next: 20 },
        rides_as_driver: 0,
        rides_as_passenger: 0,
      },
      ratings: [],
    },
  }),
  getters: {
    // En cours : deja commencees, ou prevues aujourd'hui (ou passees sans
    // avoir ete cloturees). C'est la qu'on confirme les etapes du suivi.
    active: (state) =>
      state.trackings
        .filter((t) => !isFinished(t.status) && (t.status !== "pending" || !isAfterToday(t.ride_time)))
        .sort(byRideTime),
    // A venir : confirmees par le conducteur, mais pas avant un autre jour.
    upcoming: (state) =>
      state.trackings
        .filter((t) => t.status === "pending" && isAfterToday(t.ride_time))
        .sort(byRideTime),
    // Historique : la plus recente d'abord.
    finished: (state) =>
      state.trackings.filter((t) => isFinished(t.status)).sort((a, b) => byRideTime(b, a)),
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

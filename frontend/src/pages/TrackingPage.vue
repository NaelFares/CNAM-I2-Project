<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mes courses</h1>
      <p class="page-subtitle">
        Chaque étape se confirme des deux côtés : vous et l'autre participant.
      </p>
    </header>

    <!-- Reputation : visible en haut, c'est le resultat des notes recues -->
    <Card v-if="store.loaded" class="flex flex-wrap items-center gap-4">
      <div>
        <p class="text-sm font-bold uppercase tracking-wide text-slate-500">Ma réputation</p>
        <div class="mt-1 flex items-center gap-2">
          <StarRating :value="summary.average || 0" readonly show-value />
          <span class="text-sm text-slate-500">
            {{ summary.count }} note{{ summary.count > 1 ? "s" : "" }}
          </span>
        </div>
      </div>
      <!-- Un seul palier : conduire et etre passager comptent tous les deux -->
      <div class="ml-auto text-right">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Expérience</p>
        <div class="mt-1 flex items-center justify-end gap-2">
          <TierBadge :tier="tier" />
        </div>
        <p class="mt-1 text-xs text-slate-500">
          {{ tier.rides_count }} course{{ plural(tier.rides_count) }} terminée{{ plural(tier.rides_count) }}
          <span v-if="tier.rides_to_next">· encore {{ tier.rides_to_next }} avant le palier suivant</span>
        </p>
        <p class="text-xs text-slate-400">
          {{ summary.rides_as_driver || 0 }} comme conducteur · {{ summary.rides_as_passenger || 0 }} comme passager
        </p>
      </div>

      <!-- Avis recus : replies par defaut, pour ne pas noyer la page -->
      <div v-if="receivedRatings.length" class="w-full border-t border-slate-100 pt-3">
        <button
          type="button"
          class="flex w-full items-center gap-2 text-sm font-semibold text-primary"
          @click="showRatings = !showRatings"
        >
          <ChevronRight :class="['h-4 w-4 transition', showRatings ? 'rotate-90' : '']" />
          {{ showRatings ? "Masquer les avis reçus" : `Voir les ${receivedRatings.length} avis reçus` }}
        </button>

        <RatingList v-if="showRatings" class="mt-3" :ratings="receivedRatings" />
      </div>
    </Card>

    <div v-if="!store.loaded && store.loading" class="text-sm text-slate-500">
      Chargement de vos courses…
    </div>

    <template v-else>
      <!-- Demandes de trajet : seules celles qui n'ont pas encore
           de suivi sont listees ici. Une demande confirmee bascule dans
           "En cours", ou commence le suivi de la course. -->
      <section class="space-y-4">
        <div>
          <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">Mes demandes de trajet</h2>
          <p class="text-xs text-slate-500">
            Une fois confirmée par le conducteur, la course apparaît dans « En cours ».
          </p>
        </div>

        <p v-if="app.ridesViewLoading && !app.mySelections.length" class="text-sm text-slate-500">
          Chargement de vos demandes…
        </p>
        <div v-else-if="openRequests.length" class="grid gap-2 md:grid-cols-2">
          <div
            v-for="request in openRequests"
            :key="request.selection_id"
            class="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-bold text-slate-900">Avec {{ request.driver_name }}</p>
              <p class="mt-0.5 text-xs text-slate-600">
                {{ request.ride_type === "to_campus" ? "Vers le campus" : "Depuis le campus" }}
                · {{ formatRideTime(request.ride_time) }}
              </p>
              <p
                class="mt-1 text-xs font-semibold"
                :class="request.selection_status === 'rejected' ? 'text-rose-700' : 'text-amber-700'"
              >
                {{ request.selection_status === "rejected" ? "Refusé" : "En attente du conducteur" }}
              </p>
            </div>
            <Button
              variant="secondary"
              :disabled="String(app.selectionLoadingRideId) === String(request.ride_id)"
              @click="app.cancelRideSelection(request.ride_id)"
            >
              <X class="h-4 w-4" aria-hidden="true" />
              {{ request.selection_status === "rejected" ? "Retirer" : "Annuler" }}
            </Button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">Aucune demande en attente.</p>
      </section>

      <section class="space-y-4">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">En cours</h2>
        <div v-if="store.active.length" class="grid gap-4 lg:grid-cols-2">
          <TrackingCard v-for="tracking in store.active" :key="tracking.id" :tracking="tracking" />
        </div>
        <div v-else class="advice-banner">
          Aucune course en cours. Réservez un trajet depuis la page Covoiturage pour démarrer un suivi.
        </div>
      </section>

      <section v-if="store.finished.length" class="space-y-4">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">Historique</h2>
        <div class="grid gap-4 lg:grid-cols-2">
          <TrackingCard v-for="tracking in store.finished" :key="tracking.id" :tracking="tracking" />
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ChevronRight, X } from "lucide-vue-next";

import RatingList from "../components/RatingList.vue";
import TrackingCard from "../components/TrackingCard.vue";
import { Button, Card, StarRating, TierBadge } from "../components/ui";
import { useAppStore } from "../stores/app";
import { useTrackingStore } from "../stores/tracking";

const store = useTrackingStore();
const app = useAppStore();


// Les demandes confirmees ne sont pas repetees ici : elles ont leur carte de
// suivi dans "En cours". Restent les demandes en attente et refusees.
const openRequests = computed(() =>
  app.mySelections.filter((request) => request.selection_status !== "accepted")
);

function formatRideTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Horaire non défini"
    : date.toLocaleString("fr-FR", {
        weekday: "short",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
}

const summary = computed(() => store.myRatings.summary);
const receivedRatings = computed(() => store.myRatings.ratings || []);

// Un seul palier par profil : chaque course terminee compte, que l'on ait
// conduit ou ete passager. Le detail par role montre d'ou il vient.
const tier = computed(() => summary.value.tier || {});
const plural = (count) => (count > 1 ? "s" : "");
const showRatings = ref(false);

onMounted(() => {
  store.load();
  store.loadMyRatings();
  app.loadMySelections();
});
</script>

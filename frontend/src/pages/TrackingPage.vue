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
      <!-- Un palier par role : conduire et etre passager se comptent a part -->
      <div class="ml-auto flex flex-wrap items-center gap-4">
        <div v-for="role in roles" :key="role.key" class="text-right">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ role.label }}</p>
          <div class="mt-1 flex items-center justify-end gap-2">
            <TierBadge :tier="role.tier" :role-label="role.label.toLowerCase()" />
          </div>
          <p class="mt-1 text-xs text-slate-500">
            {{ role.tier.rides_count }} course{{ role.tier.rides_count > 1 ? "s" : "" }}
            <span v-if="role.tier.rides_to_next">
              · encore {{ role.tier.rides_to_next }}
            </span>
          </p>
        </div>
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
import { ChevronRight } from "lucide-vue-next";

import RatingList from "../components/RatingList.vue";
import TrackingCard from "../components/TrackingCard.vue";
import { Card, StarRating, TierBadge } from "../components/ui";
import { useTrackingStore } from "../stores/tracking";

const store = useTrackingStore();

const summary = computed(() => store.myRatings.summary);
const receivedRatings = computed(() => store.myRatings.ratings || []);

// Les deux paliers sont toujours affiches : voir qu'on repart de zero dans
// l'autre role est une information utile, pas un manque.
const roles = computed(() => [
  { key: "driver", label: "Conducteur", tier: summary.value.driver || {} },
  { key: "passenger", label: "Passager", tier: summary.value.passenger || {} },
]);
const showRatings = ref(false);

onMounted(() => {
  store.load();
  store.loadMyRatings();
});
</script>

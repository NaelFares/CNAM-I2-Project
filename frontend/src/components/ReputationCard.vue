<template>
  <Card class="space-y-4">
    <div class="flex flex-wrap items-center gap-x-8 gap-y-4">
      <div>
        <p class="muted">Note moyenne</p>
        <div class="mt-1 flex items-center gap-2">
          <span class="text-2xl font-bold text-slate-900">{{ average }}</span>
          <StarRating :value="summary.average || 0" readonly />
          <span class="muted">({{ summary.count }} avis)</span>
        </div>
      </div>
      <!-- Un seul palier : conduire et etre passager comptent tous les deux -->
      <div>
        <p class="muted">Expérience</p>
        <div class="mt-1 flex flex-wrap items-center gap-2">
          <TierBadge :tier="tier" />
          <span class="text-sm text-slate-600">
            {{ tier.rides_count }} course{{ plural(tier.rides_count) }}
            <span class="text-slate-400">({{ summary.rides_as_driver || 0 }} en conducteur, {{ summary.rides_as_passenger || 0 }} en passager)</span>
          </span>
        </div>
        <p v-if="tier.rides_to_next" class="muted mt-1">Encore {{ tier.rides_to_next }} pour le palier suivant.</p>
      </div>
    </div>

    <!-- Avis recus : replies par defaut, pour ne pas noyer la page -->
    <div v-if="ratings.length" class="border-t border-slate-100 pt-3">
      <button type="button" class="btn-ghost -ml-3" :aria-expanded="open" @click="open = !open">
        <ChevronDown :class="['h-4 w-4 transition', open ? 'rotate-180' : '']" aria-hidden="true" />
        {{ open ? "Masquer les avis" : `Voir les ${ratings.length} avis reçus` }}
      </button>
      <RatingList v-if="open" class="mt-3" :ratings="ratings" />
    </div>
  </Card>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ChevronDown } from "lucide-vue-next";

import RatingList from "./RatingList.vue";
import { Card, StarRating, TierBadge } from "./ui";
import { useTrackingStore } from "../stores/tracking";

const store = useTrackingStore();
const open = ref(false);

const summary = computed(() => store.myRatings.summary);
const ratings = computed(() => store.myRatings.ratings || []);
const tier = computed(() => summary.value.tier || {});
const average = computed(() =>
  summary.value.average == null
    ? "—"
    : Number(summary.value.average).toLocaleString("fr-FR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
);
const plural = (count) => (count > 1 ? "s" : "");

onMounted(() => store.loadMyRatings());
</script>

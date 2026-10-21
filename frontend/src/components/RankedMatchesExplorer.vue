<template>
  <section class="matches-explorer" aria-label="Covoiturages compatibles">
    <div class="matches-explorer__results">
      <div class="flex items-center justify-between gap-3">
        <p class="text-sm text-slate-600">
          <span class="font-semibold text-slate-900">{{ displayedMatches.length }} trajet{{ displayedMatches.length > 1 ? "s" : "" }}</span>
          compatible{{ displayedMatches.length > 1 ? "s" : "" }}
        </p>
        <label class="inline-flex items-center gap-2 text-sm text-slate-500">
          <ArrowDownUp class="h-4 w-4" aria-hidden="true" />
          <span class="sr-only">Trier les trajets</span>
          <select v-model="sortMode" class="input w-auto py-1.5 pr-8 text-sm">
            <option value="compatibility">Meilleur choix</option>
            <option value="detour">Plus petit détour</option>
            <option value="departure">Heure</option>
          </select>
        </label>
      </div>

      <EmptyState
        v-if="!displayedMatches.length"
        :icon="SearchX"
        title="Aucun trajet compatible ce jour-là"
        text="Choisissez un autre jour dans le calendrier."
      />

      <ShowMore v-else :items="displayedMatches" :limit="6" item-key="key">
        <template #default="{ item: entry }">
          <RankedMatchCard
            :match="entry.match"
            :rank="entry.rank"
            :selected="entry.index === selectedIndex"
            :busy="isRideLoading(entry.match.ride_id)"
            @focus="selectMatch(entry.index)"
            @choose="$emit('choose-ride', entry.match)"
          />
        </template>
      </ShowMore>
    </div>

    <div class="matches-explorer__map-panel">
      <RouteMap
        class="matches-explorer__map"
        height="100%"
        :routes="mapRoutes"
        :selected-route-index="selectedIndex"
        :my-route-geometry="referenceGeometry"
        :estimated="referenceEstimated"
        @select-route="selectMatch"
      />

      <div class="matches-explorer__legend" aria-label="Légende de la carte">
        <span><i class="route-legend"></i> Trajet affiché</span>
        <span><i class="route-legend route-legend--muted"></i> Autres trajets</span>
        <span><i class="point-legend point-legend--pickup"></i> Prise en charge</span>
        <span><i class="point-legend point-legend--dropoff"></i> Dépose</span>
        <span><i class="point-legend point-legend--destination"></i> Destination</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { ArrowDownUp, SearchX } from "lucide-vue-next";

import RankedMatchCard from "./RankedMatchCard.vue";
import RouteMap from "./RouteMap.vue";
import { EmptyState, ShowMore } from "./ui";

const props = defineProps({
  matches: { type: Array, default: () => [] },
  referenceGeometry: { type: Array, default: () => [] },
  // Le trajet de reference (recherche rapide) a ete estime faute d'OSRM.
  referenceEstimated: { type: Boolean, default: false },
  loadingRideId: { type: [Number, String], default: null },
});

defineEmits(["choose-ride"]);

const sortMode = ref("compatibility");
const selectedIndex = ref(0);

const uniqueMatches = computed(() => {
  const byRide = new Map();
  props.matches.forEach((match, index) => {
    const key = match.ride_id == null ? `missing-${index}` : `ride-${match.ride_id}`;
    const previous = byRide.get(key);
    const isBetter = !previous
      || Number(match.score || 0) > Number(previous.score || 0)
      || (
        Number(match.score || 0) === Number(previous.score || 0)
        && Number(match.extra_time_min || 0) < Number(previous.extra_time_min || 0)
      );
    if (isBetter) byRide.set(key, match);
  });
  return [...byRide.values()];
});

const rankedMatches = computed(() => {
  const scoreOrder = [...new Set(uniqueMatches.value.map((match) => Number(match.score || 0)))].sort((a, b) => b - a);
  const rankByScore = new Map(scoreOrder.map((score, index) => [score, index + 1]));

  return uniqueMatches.value.map((match, originalIndex) => ({
    match,
    originalIndex,
    rank: rankByScore.get(Number(match.score || 0)) || scoreOrder.length + 1,
    key: `${match.ride_id || match.driver_id}-${match.passenger_id}-${match.ride_time}-${originalIndex}`,
  }));
});

const displayedMatches = computed(() => {
  const entries = [...rankedMatches.value];
  if (sortMode.value === "detour") {
    entries.sort((a, b) => Number(a.match.extra_time_min || 0) - Number(b.match.extra_time_min || 0));
  } else if (sortMode.value === "departure") {
    entries.sort((a, b) => String(a.match.ride_time || "").localeCompare(String(b.match.ride_time || "")));
  } else {
    entries.sort((a, b) => a.rank - b.rank || Number(a.match.extra_time_min || 0) - Number(b.match.extra_time_min || 0));
  }
  return entries.map((entry, index) => ({ ...entry, index }));
});

const mapRoutes = computed(() => displayedMatches.value.map((entry) => ({ ...entry.match, rank: entry.rank })));

function selectMatch(index) {
  selectedIndex.value = Math.max(0, Math.min(Number(index), displayedMatches.value.length - 1));
}

function isRideLoading(rideId) {
  return props.loadingRideId !== null && String(props.loadingRideId) === String(rideId);
}

watch(
  () => props.matches,
  () => {
    selectedIndex.value = 0;
  },
);

watch(sortMode, () => {
  selectedIndex.value = 0;
});
</script>

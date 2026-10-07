<template>
  <section class="matches-explorer" aria-label="Explorateur des covoiturages compatibles">
    <aside class="matches-explorer__results">
      <div class="matches-explorer__toolbar">
        <div>
          <strong>{{ displayedMatches.length }} trajet{{ displayedMatches.length > 1 ? "s" : "" }}</strong>
          <span>classé{{ displayedMatches.length > 1 ? "s" : "" }} par compatibilité</span>
        </div>
        <label>
          <span class="sr-only">Trier les trajets</span>
          <select v-model="sortMode" class="matches-explorer__sort">
            <option value="compatibility">Compatibilité</option>
            <option value="detour">Détour</option>
            <option value="departure">Départ</option>
          </select>
        </label>
      </div>

      <div ref="resultsList" class="matches-explorer__scroll">
        <p v-if="!displayedMatches.length" class="rounded-xl bg-white p-4 text-sm font-semibold text-slate-600">
          Aucun trajet compatible pour ce jour. Utilisez les flèches pour voir les autres jours.
        </p>
        <section v-if="goldMatches.length" class="matches-explorer__gold-group">
          <header>
            <Trophy class="matches-explorer__award-icon" aria-hidden="true" />
            <div>
              <strong>Meilleurs choix</strong>
              <small>{{ goldMatches.length }} trajet{{ goldMatches.length > 1 ? "s" : "" }} à {{ goldMatches[0].match.score }} %</small>
            </div>
          </header>
          <RankedMatchCard
            v-for="entry in goldMatches"
            :key="entry.key"
            :match="entry.match"
            :rank="entry.rank"
            :selected="entry.index === selectedIndex"
            :busy="isRideLoading(entry.match.ride_id)"
            @focus="selectMatch(entry.index)"
            @choose="$emit('choose-ride', entry.match)"
          />
        </section>

        <RankedMatchCard
          v-for="entry in remainingMatches"
          :key="entry.key"
          :match="entry.match"
          :rank="entry.rank"
          :selected="entry.index === selectedIndex"
          :busy="isRideLoading(entry.match.ride_id)"
          @focus="selectMatch(entry.index)"
          @choose="$emit('choose-ride', entry.match)"
        />
      </div>
    </aside>

    <div class="matches-explorer__map-panel">
      <RouteMap
        class="matches-explorer__map"
        height="100%"
        :routes="mapRoutes"
        :selected-route-index="selectedIndex"
        :my-route-geometry="referenceGeometry"
        @select-route="selectMatch"
      />

      <div class="matches-explorer__legend" aria-label="Légende de la carte">
        <span><i class="route-legend route-legend--selected"></i> Trajet affiché</span>
        <span><i class="route-legend route-legend--muted"></i> Autres trajets</span>
        <span><i class="point-legend point-legend--pickup"></i> Passager</span>
        <span><i class="point-legend point-legend--destination"></i> Destination</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Trophy } from "lucide-vue-next";

import RankedMatchCard from "./RankedMatchCard.vue";
import RouteMap from "./RouteMap.vue";

const props = defineProps({
  matches: { type: Array, default: () => [] },
  referenceGeometry: { type: Array, default: () => [] },
  loadingRideId: { type: [Number, String], default: null },
});

defineEmits(["choose-ride"]);

const sortMode = ref("compatibility");
const selectedIndex = ref(0);
const resultsList = ref(null);

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

const goldMatches = computed(() => displayedMatches.value.filter((entry) => entry.rank === 1));
const remainingMatches = computed(() => displayedMatches.value.filter((entry) => entry.rank !== 1));
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
    resultsList.value?.scrollTo({ top: 0, behavior: "smooth" });
  },
);

watch(sortMode, () => {
  selectedIndex.value = 0;
  resultsList.value?.scrollTo({ top: 0, behavior: "smooth" });
});
</script>

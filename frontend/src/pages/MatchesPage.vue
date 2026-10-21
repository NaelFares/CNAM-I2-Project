<template>
  <section class="page-shell">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div class="page-header">
        <h1 class="page-title">Covoiturage</h1>
        <p class="page-subtitle">{{ mode === "search" ? "Passager : trouvez une place sur le trajet d'un autre étudiant." : "Conducteur : proposez vos places et répondez aux demandes." }}</p>
      </div>
      <!-- Chacun cherche ET propose, selon le trajet -->
      <div class="segmented" role="tablist" aria-label="Rôle">
        <button type="button" role="tab" :aria-selected="mode === 'search'" @click="setMode('search')">
          <UserRound class="h-4 w-4" aria-hidden="true" />
          Passager
        </button>
        <button type="button" role="tab" :aria-selected="mode === 'drive'" @click="setMode('drive')">
          <CarFront class="h-4 w-4" aria-hidden="true" />
          Conducteur
        </button>
      </div>
    </header>

    <DriverPanel v-if="mode === 'drive'" />

    <template v-else>
      <CarpoolSearchForm v-show="!searched" @search="runSearch" />

      <template v-if="searched">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="flex items-center gap-2 text-sm text-slate-600">
            <component :is="searched === 'week' ? CalendarDays : MapPinned" class="h-4 w-4" aria-hidden="true" />
            {{ searched === "week" ? "Ma semaine de cours" : "Trajet précis" }}
          </p>
          <Button variant="secondary" size="sm" @click="resetSearch">
            <SlidersHorizontal class="h-4 w-4" aria-hidden="true" />
            Modifier la recherche
          </Button>
        </div>

        <!-- Semaine : calendrier des propositions, puis le detail du jour choisi -->
        <template v-if="searched === 'week'">
          <EmptyState
            v-if="!app.matches.length"
            :icon="SearchX"
            title="Aucun covoiturage cette semaine"
            text="Aucun conducteur ne passe près de chez vous à vos horaires. Essayez une autre semaine."
          />
          <template v-else>
            <Card>
              <WeekCalendar
                :monday="searchedWeekStart"
                :items="calendarItems"
                :navigable="false"
                selectable-days
                :active-day="activeDay"
                empty-label="Aucune proposition"
                @select-day="activeDay = $event"
              >
                <template #day-badge="{ day }">
                  <Badge v-if="day.items.length" variant="primary">{{ day.items.length }}</Badge>
                </template>
                <template #item="{ item }">
                  <button
                    type="button"
                    class="calendar-chip"
                    :class="item.outbound ? 'calendar-chip--out' : 'calendar-chip--back'"
                    @click="activeDay = item.date.slice(0, 10)"
                  >
                    <span class="font-semibold text-slate-900">{{ item.time }}</span>
                    <span class="truncate text-xs text-slate-500">{{ item.driver }}</span>
                  </button>
                </template>
              </WeekCalendar>
            </Card>

            <SectionHeader :title="activeDayLabel" />
            <RankedMatchesExplorer
              :matches="dayMatches"
              :loading-ride-id="app.selectionLoadingRideId"
              @choose-ride="chooseRide"
            />
          </template>
        </template>

        <!-- Trajet precis -->
        <template v-else>
          <RankedMatchesExplorer
            v-if="app.searchResults.length"
            :matches="app.searchResults"
            :reference-geometry="app.searchRouteGeometry"
            :reference-estimated="app.searchRouteEstimated"
            :loading-ride-id="app.selectionLoadingRideId"
            @choose-ride="chooseRide"
          />
          <EmptyState
            v-else
            :icon="SearchX"
            title="Aucun covoiturage pour ce trajet"
            text="Essayez un autre horaire, ou cherchez sur toute votre semaine."
          />
        </template>
      </template>
    </template>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CalendarDays, CarFront, MapPinned, SearchX, SlidersHorizontal, UserRound } from "lucide-vue-next";

import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import DriverPanel from "../components/DriverPanel.vue";
import RankedMatchesExplorer from "../components/RankedMatchesExplorer.vue";
import WeekCalendar from "../components/WeekCalendar.vue";
import { Badge, Button, Card, EmptyState, SectionHeader } from "../components/ui";
import { isOutbound } from "../lib/direction";
import { formatDay } from "../lib/format";
import { matchesForDay, schoolWeekDays } from "../lib/week";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const router = useRouter();
const route = useRoute();

// "search" : passager, je cherche une place ; "drive" : conducteur, je propose
// ma voiture. Le role est dans l'URL pour pouvoir y renvoyer depuis ailleurs.
const mode = ref(route.query.mode === "drive" ? "drive" : "search");

function setMode(value) {
  mode.value = value;
  router.replace({ query: value === "drive" ? { mode: "drive" } : {} });
}
// null tant qu'aucune recherche n'a abouti, sinon "week" ou "trip".
const searched = ref(null);
const searchedWeekStart = ref("");
const activeDay = ref("");

const calendarItems = computed(() =>
  app.matches.map((match, index) => {
    const date = String(match.ride_time || "").replace(" ", "T");
    return {
      key: `${match.ride_id}-${index}`,
      date,
      outbound: isOutbound(match.ride_type),
      time: date.slice(11, 16),
      driver: match.driver_name,
    };
  }),
);
const dayMatches = computed(() => matchesForDay(app.matches, activeDay.value));
const activeDayLabel = computed(() => {
  const count = dayMatches.value.length;
  const day = formatDay(`${activeDay.value}T12:00:00`);
  return `${day.charAt(0).toUpperCase()}${day.slice(1)} · ${count} proposition${count > 1 ? "s" : ""}`;
});

async function runSearch(payload) {
  if (payload.scope === "week") {
    const ok = await app.findMatches(payload.weekStart, payload.ladiesOnly);
    if (!ok) return;
    searchedWeekStart.value = payload.weekStart;
    // Ouvre le premier jour qui a des propositions.
    const days = schoolWeekDays(payload.weekStart);
    activeDay.value = (days.find((day) => matchesForDay(app.matches, day.iso).length) || days[0]).iso;
    searched.value = "week";
    return;
  }
  const ok = await app.searchCarpoolTrip(payload);
  if (ok) searched.value = "trip";
}

function resetSearch() {
  searched.value = null;
  app.matches = [];
  app.searchResults = [];
  app.searchRouteGeometry = [];
  app.searchRouteEstimated = false;
}

function chooseRide(match) {
  app.prepareRideSelection(match);
  router.push(`/matches/recap/${match.ride_id}`);
}
</script>

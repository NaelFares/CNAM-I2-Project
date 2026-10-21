<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Covoiturage</h1>
      <p class="page-subtitle">
        Cherchez une place dans la voiture de quelqu'un, ou proposez la vôtre sur vos trajets.
      </p>
    </header>

    <!-- Plus de role exclusif : chacun cherche ET propose, selon le trajet -->
    <div class="grid grid-cols-2 gap-2 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm">
      <button
        type="button"
        :class="['flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-bold transition', mode === 'search' ? 'bg-blue-700 text-white' : 'text-slate-600 hover:bg-slate-100']"
        @click="mode = 'search'"
      >
        <UsersRound class="h-4 w-4" aria-hidden="true" />
        Je cherche une place
      </button>
      <button
        type="button"
        :class="['flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-bold transition', mode === 'drive' ? 'bg-blue-700 text-white' : 'text-slate-600 hover:bg-slate-100']"
        @click="mode = 'drive'"
      >
        <CarFront class="h-4 w-4" aria-hidden="true" />
        Je propose ma voiture
      </button>
    </div>

    <!-- Je propose ma voiture : formulaire, trajets proposes et suggestions -->
    <DriverPanel v-if="mode === 'drive'" />

    <template v-else>
      <!-- Les demandes et leur suivi vivent desormais sur la page Mes courses -->
      <RouterLink
        to="/tracking"
        class="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
      >
        <span class="flex items-center gap-2">
          <CircleCheckBig class="h-5 w-5 shrink-0 text-blue-700" aria-hidden="true" />
          Vos demandes de trajet et leur suivi sont dans « Mes courses »
        </span>
        <ChevronRight class="h-4 w-4 shrink-0" aria-hidden="true" />
      </RouterLink>

      <div class="flex flex-wrap gap-2">
        <Button :variant="activeTab === 'quick' ? 'primary' : 'secondary'" @click="activeTab = 'quick'">
          Recherche rapide
        </Button>
        <Button :variant="activeTab === 'planning' ? 'primary' : 'secondary'" @click="activeTab = 'planning'">
          Recherche par semaine
        </Button>
      </div>

      <div v-show="activeTab === 'quick'" class="space-y-4">
        <div class="advice-banner">
          Départ et arrivée sont pré-remplis depuis votre profil. Modifiez-les pour un trajet ponctuel.
        </div>

        <CarpoolSearchForm v-if="!quickSearchPerformed" @search="runQuickSearch" />

        <template v-else>
          <div class="flex justify-end">
            <Button variant="secondary" @click="resetQuickSearch">Nouvelle recherche</Button>
          </div>

          <RankedMatchesExplorer
            v-if="app.searchResults.length"
            :matches="app.searchResults"
            :reference-geometry="app.searchRouteGeometry"
            :reference-estimated="app.searchRouteEstimated"
            :loading-ride-id="app.selectionLoadingRideId"
            @choose-ride="chooseRide"
          />

          <Card v-else>
            <p class="text-sm font-semibold text-slate-700">Aucun covoiturage compatible n’a été trouvé pour ce trajet.</p>
          </Card>
        </template>
      </div>

      <div v-show="activeTab === 'planning'" class="space-y-4">
        <div class="advice-banner">
          Choisissez une semaine de votre planning pour rechercher des covoiturages.
        </div>

        <Card v-if="!planningSearchPerformed" class="space-y-4">
          <div>
            <label for="planning-week" class="mb-1 block text-sm font-bold text-slate-800">Semaine à rechercher</label>
            <input id="planning-week" v-model="selectedWeekDate" type="date" class="input max-w-xs" />
            <p class="mt-2 text-sm text-slate-600">Du {{ selectedWeekDays[0]?.label }} au {{ selectedWeekDays[4]?.label }}.</p>
          </div>
          <label v-if="ladiesOnlyAvailable" class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <input v-model="ladiesOnly" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300" />
            <span>
              <span class="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                <Venus class="h-4 w-4 text-pink-600" aria-hidden="true" />
                Covoiturer entre femmes
              </span>
              <span class="mt-0.5 block text-xs text-slate-500">
                Cette recherche ne proposera que des conductrices.
              </span>
            </span>
          </label>

          <Button :disabled="app.loading || !selectedWeekStart" @click="runPlanningSearch">
            <UsersRound class="h-4 w-4" aria-hidden="true" />
            Rechercher cette semaine
          </Button>
        </Card>

        <template v-else>
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-semibold text-slate-700">Semaine du {{ searchedDays[0]?.label }} au {{ searchedDays[4]?.label }}</p>
            <Button variant="secondary" @click="resetPlanningSearch">Nouvelle recherche</Button>
          </div>

          <div v-if="app.matches.length" class="planning-day-results">
            <div class="planning-day-results__header">
              <button type="button" class="planning-day-results__arrow" :disabled="activeDayIndex === 0" aria-label="Jour précédent" @click="activeDayIndex--">
                <ChevronLeft class="h-5 w-5" aria-hidden="true" />
              </button>
              <div class="text-center">
                <p class="text-xs font-bold uppercase tracking-wide text-blue-700">{{ activeDayIndex + 1 }} / {{ searchedDays.length }}</p>
                <h2 class="text-base font-bold capitalize text-slate-900">{{ activeDay?.label }}</h2>
              </div>
              <button type="button" class="planning-day-results__arrow" :disabled="activeDayIndex === searchedDays.length - 1" aria-label="Jour suivant" @click="activeDayIndex++">
                <ChevronRight class="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <RankedMatchesExplorer
              :matches="dayMatches"
              :loading-ride-id="app.selectionLoadingRideId"
              @choose-ride="chooseRide"
            />
          </div>

          <Card v-else>
            <p class="text-sm font-semibold text-slate-700">Aucun covoiturage compatible n’a été trouvé pour cette semaine.</p>
          </Card>
        </template>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { CarFront, ChevronLeft, ChevronRight, CircleCheckBig, UsersRound, Venus } from "lucide-vue-next";

import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import DriverPanel from "../components/DriverPanel.vue";
import RankedMatchesExplorer from "../components/RankedMatchesExplorer.vue";
import { Button, Card } from "../components/ui";
import { localDateIso, matchesForDay, mondayIso, nextUpcomingEvent, schoolWeekDays } from "../lib/week";
import { useAppStore } from "../stores/app";
import { canUseLadiesOnly } from "../lib/gender";

const app = useAppStore();
const ladiesOnly = ref(false);
const ladiesOnlyAvailable = computed(() => canUseLadiesOnly(app.profile));
const router = useRouter();
const activeTab = ref("quick");
const quickSearchPerformed = ref(false);
const planningSearchPerformed = ref(false);
const selectedWeekDate = ref(localDateIso());
const selectedWeekStart = computed(() => mondayIso(selectedWeekDate.value));
const selectedWeekDays = computed(() => schoolWeekDays(selectedWeekStart.value));
const searchedWeekStart = ref(null);
const searchedDays = computed(() => schoolWeekDays(searchedWeekStart.value));
const activeDayIndex = ref(0);
const activeDay = computed(() => searchedDays.value[activeDayIndex.value]);
const dayMatches = computed(() => matchesForDay(app.matches, activeDay.value?.iso));
// "search" : je cherche une place ; "drive" : je propose ma voiture.
const mode = ref("search");

onMounted(async () => {
  if (!app.profile) app.loadProfile();
  // La recherche par semaine s'ouvre sur la semaine du prochain cours : la
  // semaine en cours est souvent deja passee ou vide (apres un import CSV,
  // les cours peuvent etre plusieurs semaines plus loin).
  await app.loadScheduleEvents();
  const nextEvent = nextUpcomingEvent(app.events);
  if (nextEvent) selectedWeekDate.value = String(nextEvent.start_time).slice(0, 10);
});

async function runQuickSearch(payload) {
  const ok = await app.searchCarpoolTrip(payload);
  if (ok) quickSearchPerformed.value = true;
}

function resetQuickSearch() {
  quickSearchPerformed.value = false;
  app.searchResults = [];
  app.searchRouteGeometry = [];
  app.searchRouteEstimated = false;
}

async function runPlanningSearch() {
  const weekStart = selectedWeekStart.value;
  if (!weekStart) return;
  // La case n'est affichee qu'aux utilisatrices, mais on ne se fie pas au
  // rendu : le flag est neutralise si le profil ne le permet pas.
  const matchesFound = await app.findMatches(
    weekStart,
    ladiesOnlyAvailable.value && ladiesOnly.value,
  );
  if (!matchesFound) return;
  searchedWeekStart.value = weekStart;
  const firstDayWithMatches = schoolWeekDays(weekStart).findIndex(
    (day) => matchesForDay(app.matches, day.iso).length > 0,
  );
  activeDayIndex.value = Math.max(0, firstDayWithMatches);
  planningSearchPerformed.value = true;
}

function resetPlanningSearch() {
  planningSearchPerformed.value = false;
  app.matches = [];
  searchedWeekStart.value = null;
  activeDayIndex.value = 0;
}

function chooseRide(match) {
  app.prepareRideSelection(match);
  router.push(`/matches/recap/${match.ride_id}`);
}
</script>

<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">{{ isDriver ? "Mes trajets proposés" : "Covoiturage" }}</h1>
      <p class="page-subtitle">
        {{ isDriver
          ? "Acceptez ou refusez les demandes de passagers pour vos trajets."
          : "Trouvez un trajet compatible et demandez une place au conducteur." }}
      </p>
    </header>

    <template v-if="isDriver">
      <Card v-if="app.ridesViewLoading" class="text-sm font-semibold text-slate-600">
        Chargement de vos trajets proposés...
      </Card>

      <Card v-else-if="!app.driverOffers.length" class="space-y-4">
        <div>
          <h2 class="text-lg font-bold text-slate-900">Aucun trajet proposé</h2>
          <p class="mt-1 text-sm text-slate-600">
            Importez d'abord votre planning, puis générez les trajets associés.
          </p>
        </div>
        <Button :disabled="app.loading" @click="generateDriverOffers">
          <CarFront class="h-4 w-4" aria-hidden="true" />
          Générer mes trajets
        </Button>
      </Card>

      <div v-else class="space-y-4">
        <div class="flex items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
          <button type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-300 text-blue-700 hover:bg-blue-50" aria-label="Semaine précédente" @click="changeDriverWeek(-1)">
            <ChevronLeft class="h-5 w-5" aria-hidden="true" />
          </button>
          <div class="min-w-0 flex-1 text-center">
            <p class="text-xs font-bold uppercase tracking-wide text-blue-700">Mes trajets proposés</p>
            <h2 class="text-sm font-bold text-slate-900 sm:text-base">Du {{ driverWeekDays[0]?.label }} au {{ driverWeekDays[6]?.label }}</h2>
          </div>
          <button type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-300 text-blue-700 hover:bg-blue-50" aria-label="Semaine suivante" @click="changeDriverWeek(1)">
            <ChevronRight class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <Card v-if="!driverOffersForWeek.length" class="text-sm font-semibold text-slate-600">
          Aucun trajet proposé pour cette semaine. Utilisez les flèches pour voir une autre semaine.
        </Card>

        <div v-else class="grid gap-4 lg:grid-cols-2">
        <Card v-for="ride in driverOffersForWeek" :key="ride.id" class="space-y-4">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-wide text-blue-700">{{ directionLabel(ride.ride_type) }}</p>
              <h2 class="mt-1 text-base font-bold text-slate-900">{{ formatRideTime(ride.ride_time) }}</h2>
            </div>
            <span
              class="rounded-full px-3 py-1 text-xs font-bold"
              :class="ride.available_seats ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'"
            >
              {{ ride.available_seats ? seatsLabel(ride.available_seats) : "Complet" }}
            </span>
          </div>

          <div class="flex items-center gap-2 text-sm font-semibold text-slate-600">
            <UsersRound class="h-4 w-4 text-blue-700" aria-hidden="true" />
            {{ ride.occupied_seats }} / {{ ride.car_seats }} place{{ ride.car_seats > 1 ? "s" : "" }} réservée{{ ride.occupied_seats > 1 ? "s" : "" }}
          </div>

          <div v-if="ride.passengers.length" class="space-y-2 border-t border-slate-200 pt-3">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Demandes et passagers</p>
            <div
              v-for="passenger in ride.passengers"
              :key="passenger.id"
              class="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-2"
            >
              <UserRoundCheck class="h-5 w-5 shrink-0 text-blue-700" aria-hidden="true" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-bold text-slate-800">{{ passenger.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ passenger.email }}</p>
                <p class="text-xs font-semibold" :class="passenger.selection_status === 'accepted' ? 'text-emerald-700' : passenger.selection_status === 'rejected' ? 'text-rose-700' : 'text-amber-700'">
                  {{ selectionStatusLabel(passenger.selection_status) }}
                </p>
              </div>
              <div v-if="passenger.selection_status !== 'rejected'" class="flex shrink-0 items-center gap-1">
                <button
                  v-if="passenger.selection_status === 'pending'"
                  type="button"
                  class="rounded-lg p-2 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                  :disabled="app.selectionLoadingRideId === ride.id"
                  :aria-label="`Accepter ${passenger.name}`"
                  :title="`Accepter ${passenger.name}`"
                  @click="app.decidePassenger(ride.id, passenger.id, 'accept')"
                >
                  <Check class="h-5 w-5" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  class="rounded-lg p-2 text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                  :disabled="app.selectionLoadingRideId === ride.id"
                  :aria-label="`Refuser ${passenger.name}`"
                  :title="`Refuser ${passenger.name}`"
                  @click="app.decidePassenger(ride.id, passenger.id, 'reject')"
                >
                  <X class="h-5 w-5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
          <p v-else class="border-t border-slate-200 pt-3 text-sm text-slate-500">Aucune demande pour le moment.</p>
        </Card>
        </div>
      </div>
    </template>

    <template v-else>
      <Card class="space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Mes demandes de trajet</h2>
            <p class="text-sm text-slate-600">Suivez la réponse du conducteur à vos demandes.</p>
          </div>
          <CircleCheckBig class="h-6 w-6 shrink-0 text-blue-700" aria-hidden="true" />
        </div>

        <p v-if="app.ridesViewLoading" class="text-sm font-semibold text-slate-500">Chargement...</p>
        <p v-else-if="!app.mySelections.length" class="text-sm text-slate-500">Vous n'avez encore demandé aucun trajet.</p>
        <div v-else class="grid gap-2 md:grid-cols-2">
          <div
            v-for="ride in app.mySelections"
            :key="ride.selection_id"
            class="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-bold text-slate-900">Avec {{ ride.driver_name }}</p>
              <p class="mt-0.5 text-xs text-slate-600">{{ directionLabel(ride.ride_type) }} · {{ formatRideTime(ride.ride_time) }}</p>
              <p class="mt-1 text-xs font-semibold" :class="ride.selection_status === 'accepted' ? 'text-emerald-700' : ride.selection_status === 'rejected' ? 'text-rose-700' : 'text-amber-700'">
                {{ selectionStatusLabel(ride.selection_status) }}
              </p>
            </div>
            <Button
              variant="secondary"
              :disabled="String(app.selectionLoadingRideId) === String(ride.ride_id)"
              @click="app.cancelRideSelection(ride.ride_id)"
            >
              <X class="h-4 w-4" aria-hidden="true" />
              Annuler
            </Button>
          </div>
        </div>
      </Card>

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
import { useRouter } from "vue-router";
import { CarFront, Check, ChevronLeft, ChevronRight, CircleCheckBig, UserRoundCheck, UsersRound, X } from "lucide-vue-next";

import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import RankedMatchesExplorer from "../components/RankedMatchesExplorer.vue";
import { Button, Card } from "../components/ui";
import { calendarWeekDays, localDateIso, matchesForDay, mondayIso, ridesForWeek, schoolWeekDays, shiftWeek } from "../lib/week";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";

const app = useAppStore();
const auth = useAuthStore();
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
const isDriver = computed(() => auth.user?.role === "driver");
const driverWeekStart = ref(mondayIso(localDateIso()));
const driverWeekDays = computed(() => calendarWeekDays(driverWeekStart.value));
const driverOffersForWeek = computed(() => ridesForWeek(app.driverOffers, driverWeekStart.value));

onMounted(() => {
  if (isDriver.value) app.loadDriverOffers();
  else app.loadMySelections();
});

async function runQuickSearch(payload) {
  const ok = await app.searchCarpoolTrip(payload);
  if (ok) quickSearchPerformed.value = true;
}

function resetQuickSearch() {
  quickSearchPerformed.value = false;
  app.searchResults = [];
  app.searchRouteGeometry = [];
}

async function runPlanningSearch() {
  const weekStart = selectedWeekStart.value;
  if (!weekStart) return;
  const matchesFound = await app.findMatches(weekStart);
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

async function generateDriverOffers() {
  const generated = await app.generateRides();
  if (generated) await app.loadDriverOffers();
}

function directionLabel(rideType) {
  return rideType === "from_campus" ? "Retour du campus" : "Aller vers le campus";
}

function seatsLabel(count) {
  return `${count} place${count > 1 ? "s" : ""} restante${count > 1 ? "s" : ""}`;
}

function changeDriverWeek(offset) {
  driverWeekStart.value = shiftWeek(driverWeekStart.value, offset);
}

function selectionStatusLabel(status) {
  if (status === "accepted") return "Confirmé";
  if (status === "rejected") return "Refusé";
  return "En attente du conducteur";
}

function formatRideTime(value) {
  if (!value) return "Horaire non défini";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
</script>

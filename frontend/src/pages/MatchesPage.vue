<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">{{ isDriver ? "Mes trajets proposés" : "Covoiturage" }}</h1>
      <p class="page-subtitle">
        {{ isDriver
          ? "Consultez les places restantes et les passagers inscrits à vos trajets."
          : "Trouvez puis sélectionnez un trajet compatible avec vos horaires." }}
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

      <div v-else class="grid gap-4 lg:grid-cols-2">
        <Card v-for="ride in app.driverOffers" :key="ride.id" class="space-y-4">
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
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Passagers inscrits</p>
            <div
              v-for="passenger in ride.passengers"
              :key="passenger.id"
              class="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-2"
            >
              <UserRoundCheck class="h-5 w-5 shrink-0 text-blue-700" aria-hidden="true" />
              <div class="min-w-0">
                <p class="truncate text-sm font-bold text-slate-800">{{ passenger.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ passenger.email }}</p>
              </div>
            </div>
          </div>
          <p v-else class="border-t border-slate-200 pt-3 text-sm text-slate-500">Aucun passager inscrit pour le moment.</p>
        </Card>
      </div>
    </template>

    <template v-else>
      <Card class="space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Mes trajets sélectionnés</h2>
            <p class="text-sm text-slate-600">Les places que vous avez réservées auprès d'un conducteur.</p>
          </div>
          <CircleCheckBig class="h-6 w-6 shrink-0 text-blue-700" aria-hidden="true" />
        </div>

        <p v-if="app.ridesViewLoading" class="text-sm font-semibold text-slate-500">Chargement...</p>
        <p v-else-if="!app.mySelections.length" class="text-sm text-slate-500">Vous n'avez encore sélectionné aucun trajet.</p>
        <div v-else class="grid gap-2 md:grid-cols-2">
          <div
            v-for="ride in app.mySelections"
            :key="ride.selection_id"
            class="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-bold text-slate-900">Avec {{ ride.driver_name }}</p>
              <p class="mt-0.5 text-xs text-slate-600">{{ directionLabel(ride.ride_type) }} · {{ formatRideTime(ride.ride_time) }}</p>
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
          Tout mon planning
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
          Conseil: plus le profil et le planning sont précis, plus le score de compatibilité est fiable.
        </div>

        <Card v-if="!planningSearchPerformed">
          <Button :disabled="app.loading" @click="runFullPlanningSearch">
            <UsersRound class="h-4 w-4" aria-hidden="true" />
            Trouver un covoiturage
          </Button>
        </Card>

        <template v-else>
          <div class="flex justify-end">
            <Button variant="secondary" @click="resetPlanningSearch">Nouvelle recherche</Button>
          </div>

          <RankedMatchesExplorer
            v-if="app.matches.length"
            :matches="app.matches"
            :loading-ride-id="app.selectionLoadingRideId"
            @choose-ride="chooseRide"
          />

          <Card v-else>
            <p class="text-sm font-semibold text-slate-700">Aucun covoiturage compatible n’a été trouvé dans votre planning.</p>
          </Card>
        </template>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { CarFront, CircleCheckBig, UserRoundCheck, UsersRound, X } from "lucide-vue-next";

import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import RankedMatchesExplorer from "../components/RankedMatchesExplorer.vue";
import { Button, Card } from "../components/ui";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";

const app = useAppStore();
const auth = useAuthStore();
const router = useRouter();
const activeTab = ref("quick");
const quickSearchPerformed = ref(false);
const planningSearchPerformed = ref(false);
const isDriver = computed(() => auth.user?.role === "driver");

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

async function runFullPlanningSearch() {
  const ok = await app.generateRides();
  if (!ok) return;

  const matchesFound = await app.findMatches();
  if (matchesFound) planningSearchPerformed.value = true;
}

function resetPlanningSearch() {
  planningSearchPerformed.value = false;
  app.matches = [];
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

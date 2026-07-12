<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Covoiturage</h1>
      <p class="page-subtitle">Trouvez des covoitureurs compatibles selon vos trajets et horaires.</p>
    </header>

    <div class="flex gap-2">
      <Button :variant="activeTab === 'quick' ? 'primary' : 'secondary'" @click="activeTab = 'quick'">
        Recherche rapide
      </Button>
      <Button :variant="activeTab === 'planning' ? 'primary' : 'secondary'" @click="activeTab = 'planning'">
        Tout mon planning
      </Button>
    </div>

    <div v-show="activeTab === 'quick'" class="space-y-4">
      <div class="advice-banner">
        Départ et arrivée sont pré-remplis depuis votre profil — modifiez-les pour un trajet ponctuel.
      </div>

      <CarpoolSearchForm @search="app.searchCarpoolTrip" />

      <div v-if="app.searchResults.length" class="flex flex-col gap-4">
        <CarpoolResultCard
          v-for="match in app.searchResults"
          :key="`${match.driver_id}-${match.passenger_id}-${match.ride_time}`"
          :match="match"
          :my-route-geometry="app.searchRouteGeometry"
        />
      </div>
    </div>

    <div v-show="activeTab === 'planning'" class="space-y-4">
      <div class="advice-banner">
        Conseil: plus le profil et le planning sont précis, plus le score de compatibilité est fiable.
      </div>

      <Card>
        <Button :disabled="app.loading" @click="runFullPlanningSearch">
          <UsersRound class="h-4 w-4" />
          Trouver un covoiturage
        </Button>
      </Card>

      <div v-if="app.matches.length" class="grid gap-4 md:grid-cols-2">
        <article
          v-for="match in app.matches"
          :key="`${match.driver_id}-${match.passenger_id}-${match.ride_time}`"
          class="card overflow-hidden p-0"
        >
          <div class="p-5">
            <div class="mb-2 flex items-center justify-between gap-3">
              <h3 class="text-lg font-bold text-slate-900">{{ match.score }}% de compatibilité</h3>
              <Badge variant="primary">{{ match.ride_type }}</Badge>
            </div>
            <p class="text-sm font-semibold text-slate-700">{{ match.driver_name }} → {{ match.passenger_name }}</p>
            <div class="mt-2 space-y-1 text-sm text-slate-600">
              <p>Départ&nbsp;: {{ match.ride_time }}</p>
              <p>Écart de temps&nbsp;: {{ match.time_diff_min }} min</p>
              <p>Détour pour récupérer le passager&nbsp;: +{{ match.extra_time_min.toFixed(1) }} min</p>
              <p>Distance des départs&nbsp;: {{ match.distance_km.toFixed(2) }} km</p>
            </div>

            <!-- Légende couleurs -->
            <div class="mt-3 flex flex-wrap gap-3 text-xs font-medium text-slate-600">
              <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-green-500"></span>Conducteur</span>
              <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-orange-500"></span>Passager</span>
              <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-red-500"></span>Destination</span>
            </div>
          </div>

          <RouteMap
            :route-geometry="match.route_geometry"
            :driver-coords="match.driver_coords"
            :passenger-coords="match.passenger_coords"
            :dest-coords="match.campus_coords"
          />
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { UsersRound } from "lucide-vue-next";

import CarpoolResultCard from "../components/CarpoolResultCard.vue";
import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import RouteMap from "../components/RouteMap.vue";
import { Badge, Button, Card } from "../components/ui";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const activeTab = ref("quick");

async function runFullPlanningSearch() {
  const ok = await app.generateRides();
  if (ok) await app.findMatches();
}
</script>

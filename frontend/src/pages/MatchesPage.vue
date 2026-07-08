<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Correspondances</h1>
      <p class="page-subtitle">Trouvez des covoitureurs compatibles selon vos trajets et horaires.</p>
    </header>

    <div class="advice-banner">
      Conseil: plus le profil et le planning sont précis, plus le score de compatibilité est fiable.
    </div>

    <div class="card p-6">
      <button class="btn-primary" :disabled="app.loading" @click="app.findMatches">
        <UsersRound class="h-4 w-4" />
        Rechercher des correspondances
      </button>
    </div>

    <div v-if="app.matches.length" class="grid gap-4 md:grid-cols-2">
      <article
        v-for="match in app.matches"
        :key="`${match.driver_id}-${match.passenger_id}-${match.ride_time}`"
        class="card overflow-hidden p-0"
      >
        <div class="p-5">
          <div class="mb-2 flex items-center justify-between gap-3">
            <h3 class="text-lg font-bold text-slate-900">{{ match.score }}% de compatibilité</h3>
            <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">{{ match.ride_type }}</span>
          </div>
          <p class="text-sm font-semibold text-slate-700">{{ match.driver_name }} → {{ match.passenger_name }}</p>
          <div class="mt-2 space-y-1 text-sm text-slate-600">
            <p>Départ&nbsp;: {{ match.ride_time }}</p>
            <p>Écart de temps&nbsp;: {{ match.time_diff_min }} min</p>
            <p>Distance passager ↔ trajet&nbsp;: {{ match.distance_km.toFixed(2) }} km</p>
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
  </section>
</template>

<script setup>
import { UsersRound } from "lucide-vue-next";

import RouteMap from "../components/RouteMap.vue";
import { useAppStore } from "../stores/app";

const app = useAppStore();
</script>

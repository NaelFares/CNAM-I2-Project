<template>
  <article class="card overflow-hidden p-0">
    <div class="p-5">
      <div class="mb-2 flex items-center justify-between gap-3">
        <h3 class="text-lg font-bold text-slate-900">{{ match.score }}% de compatibilité</h3>
        <Badge variant="primary">{{ match.ride_type }}</Badge>
      </div>
      <p class="text-sm font-semibold text-slate-700">{{ match.driver_name }} → {{ match.passenger_name }}</p>
      <div class="mt-2 space-y-1 text-sm text-slate-600">
        <p>Départ&nbsp;: {{ match.ride_time }}</p>
        <p>Écart de temps&nbsp;: {{ match.time_diff_min }} min</p>
        <p>Distance passager ↔ trajet&nbsp;: {{ match.distance_km.toFixed(2) }} km</p>
      </div>

      <!-- Légende -->
      <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-medium text-slate-600">
        <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-green-500"></span>Conducteur</span>
        <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-orange-500"></span>Passager</span>
        <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-full bg-red-500"></span>Destination</span>
        <span class="flex items-center gap-1.5"><span class="inline-block h-0.5 w-4 bg-primary"></span>Itinéraire proposé</span>
        <span class="flex items-center gap-1.5"><span class="inline-block h-0.5 w-4 border-t-2 border-dashed" style="border-color: #7c3aed"></span>Notre itinéraire</span>
      </div>
    </div>

    <button type="button" class="block w-full cursor-zoom-in" @click="expanded = true">
      <RouteMap
        :route-geometry="match.route_geometry"
        :my-route-geometry="myRouteGeometry"
        :driver-coords="match.driver_coords"
        :passenger-coords="match.passenger_coords"
        :dest-coords="match.campus_coords"
      />
    </button>

    <Teleport to="body">
      <div v-if="expanded" class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/60 p-4" @click.self="expanded = false">
        <div class="w-full max-w-3xl rounded-2xl bg-white p-4 shadow-2xl">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-base font-bold text-slate-900">{{ match.driver_name }} → {{ match.passenger_name }}</h3>
            <button type="button" class="rounded-full p-1.5 text-slate-500 hover:bg-slate-100" @click="expanded = false">
              <X class="h-5 w-5" />
            </button>
          </div>
          <RouteMap
            height="60vh"
            :route-geometry="match.route_geometry"
            :my-route-geometry="myRouteGeometry"
            :driver-coords="match.driver_coords"
            :passenger-coords="match.passenger_coords"
            :dest-coords="match.campus_coords"
          />
        </div>
      </div>
    </Teleport>
  </article>
</template>

<script setup>
import { ref } from "vue";
import { X } from "lucide-vue-next";

import RouteMap from "./RouteMap.vue";
import { Badge } from "./ui";

defineProps({
  match: { type: Object, required: true },
  myRouteGeometry: { type: Array, default: () => [] },
});

const expanded = ref(false);
</script>

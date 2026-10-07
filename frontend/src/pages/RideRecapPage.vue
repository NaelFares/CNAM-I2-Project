<template>
  <section class="page-shell">
    <header class="page-header">
      <Button variant="secondary" @click="goBack">
        <ArrowLeft class="h-4 w-4" aria-hidden="true" />
        Retour aux trajets
      </Button>
      <div class="mt-4">
        <h1 class="page-title">Récapitulatif du trajet</h1>
        <p class="page-subtitle">Vérifiez les informations avant d'envoyer votre demande au conducteur.</p>
      </div>
    </header>

    <Card v-if="!ride" class="space-y-4">
      <div>
        <h2 class="text-lg font-bold text-slate-900">Trajet introuvable</h2>
        <p class="mt-1 text-sm text-slate-600">
          Ce récapitulatif n'est plus disponible. Revenez aux résultats et choisissez de nouveau un trajet.
        </p>
      </div>
      <Button @click="goBack">Retour aux trajets proposés</Button>
    </Card>

    <template v-else>
      <div class="grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
        <Card class="space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-wide text-blue-700">Itinéraire proposé</p>
              <h2 class="mt-1 text-lg font-bold text-slate-900">{{ directionLabel }}</h2>
            </div>
            <span class="rounded-full bg-blue-50 px-3 py-1.5 text-sm font-bold text-blue-800">
              {{ ride.score }} % compatible
            </span>
          </div>

          <RouteMap
            :route-geometry="ride.route_geometry || []"
            :passenger-coords="ride.passenger_coords || null"
            :dest-coords="ride.campus_coords || null"
            height="430px"
            route-label="Trajet sélectionné"
          />

          <div class="grid gap-3 sm:grid-cols-3">
            <div class="rounded-xl bg-slate-50 p-3">
              <Clock3 class="h-5 w-5 text-blue-700" aria-hidden="true" />
              <p class="mt-2 text-xs font-bold uppercase tracking-wide text-slate-500">Départ</p>
              <p class="mt-1 text-sm font-bold text-slate-900">{{ formattedRideTime }}</p>
            </div>
            <div class="rounded-xl bg-slate-50 p-3">
              <RouteIcon class="h-5 w-5 text-blue-700" aria-hidden="true" />
              <p class="mt-2 text-xs font-bold uppercase tracking-wide text-slate-500">Détour conducteur</p>
              <p class="mt-1 text-sm font-bold text-slate-900">+{{ formattedDetour }} min</p>
            </div>
            <div class="rounded-xl bg-slate-50 p-3">
              <MapPin class="h-5 w-5 text-blue-700" aria-hidden="true" />
              <p class="mt-2 text-xs font-bold uppercase tracking-wide text-slate-500">Distance au départ</p>
              <p class="mt-1 text-sm font-bold text-slate-900">{{ formattedDistance }} km</p>
            </div>
          </div>
        </Card>

        <div class="space-y-5">
          <Card class="space-y-4">
            <div class="flex items-center gap-2">
              <UsersRound class="h-5 w-5 text-blue-700" aria-hidden="true" />
              <h2 class="text-lg font-bold text-slate-900">Personnes du trajet</h2>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-blue-100 text-sm font-bold text-blue-800">
                  {{ initials(ride.driver_name) }}
                </span>
                <div class="min-w-0">
                  <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Conducteur</p>
                  <p class="truncate font-bold text-slate-900">{{ ride.driver_name }}</p>
                </div>
              </div>

              <div class="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-orange-100 text-sm font-bold text-orange-800">
                  {{ initials(ride.passenger_name) }}
                </span>
                <div class="min-w-0">
                  <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Passager</p>
                  <p class="truncate font-bold text-slate-900">{{ ride.passenger_name }}</p>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 border-t border-slate-200 pt-4 text-sm font-semibold text-slate-700">
              <CarFront class="h-5 w-5 text-emerald-700" aria-hidden="true" />
              {{ seatsLabel }} actuellement
            </div>
          </Card>

          <Card class="space-y-4 border-blue-200 bg-blue-50/60">
            <div class="flex items-start gap-3">
              <ShieldCheck class="mt-0.5 h-6 w-6 shrink-0 text-blue-700" aria-hidden="true" />
              <div>
                <h2 class="font-bold text-slate-900">Accord du conducteur nécessaire</h2>
                <p class="mt-1 text-sm text-slate-600">
                  Votre demande sera envoyée au conducteur. Votre place ne sera réservée que s'il l'accepte.
                </p>
              </div>
            </div>

            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button variant="secondary" :disabled="isConfirming" @click="goBack">Annuler</Button>
              <Button :disabled="isConfirming" @click="confirmRide">
                <LoaderCircle v-if="isConfirming" class="h-4 w-4 animate-spin" aria-hidden="true" />
                <CircleCheckBig v-else class="h-4 w-4" aria-hidden="true" />
                {{ isConfirming ? "Envoi..." : "Demander une place" }}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  CarFront,
  CircleCheckBig,
  Clock3,
  LoaderCircle,
  MapPin,
  Route as RouteIcon,
  ShieldCheck,
  UsersRound,
} from "lucide-vue-next";

import RouteMap from "../components/RouteMap.vue";
import { Button, Card } from "../components/ui";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const route = useRoute();
const router = useRouter();

const ride = computed(() => {
  const pending = app.pendingRide;
  return pending && String(pending.ride_id) === String(route.params.rideId) ? pending : null;
});

const isConfirming = computed(
  () => ride.value && String(app.selectionLoadingRideId) === String(ride.value.ride_id),
);
const directionLabel = computed(() => {
  const value = String(ride.value?.ride_type || "");
  if (value === "to_campus") return "Aller vers le campus";
  if (value === "from_campus") return "Retour depuis le campus";
  return value || "Trajet proposé";
});
const formattedRideTime = computed(() => ride.value?.ride_time || "Horaire non défini");
const formattedDetour = computed(() => Number(ride.value?.extra_time_min || 0).toFixed(1));
const formattedDistance = computed(() => Number(ride.value?.distance_km || 0).toFixed(1));
const availableSeats = computed(() => {
  const value = Number(ride.value?.available_seats ?? ride.value?.car_seats);
  return Number.isFinite(value) ? Math.max(0, value) : 0;
});
const seatsLabel = computed(
  () => `${availableSeats.value} place${availableSeats.value > 1 ? "s" : ""} restante${availableSeats.value > 1 ? "s" : ""}`,
);

function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function goBack() {
  app.clearPendingRide();
  router.push("/matches");
}

async function confirmRide() {
  if (!ride.value || isConfirming.value) return;
  const selected = await app.selectRide(ride.value.ride_id);
  if (selected) router.replace("/matches");
}
</script>

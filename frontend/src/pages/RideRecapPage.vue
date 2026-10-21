<template>
  <section v-if="ride" class="page-shell">
    <header class="page-header">
      <RouterLink to="/matches" class="btn-ghost -ml-3 mb-2" @click="app.clearPendingRide()">
        <ArrowLeft class="h-4 w-4" aria-hidden="true" />
        Résultats
      </RouterLink>
      <div class="flex flex-wrap items-center gap-3">
        <h1 class="page-title">Confirmer la demande</h1>
        <DirectionBadge :ride-type="ride.ride_type" />
      </div>
      <p class="page-subtitle">Votre place n'est réservée qu'une fois la demande acceptée par le conducteur.</p>
    </header>

    <div class="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(300px,1fr)]">
      <Card padding="none" class="overflow-hidden">
        <RouteMap
          :route-geometry="ride.route_geometry || []"
          :passenger-coords="ride.passenger_coords || null"
          :dropoff-coords="ride.passenger_dropoff_coords || null"
          :dest-coords="ride.campus_coords || null"
          height="420px"
          route-label="Trajet sélectionné"
          :estimated="Boolean(ride.route_estimated)"
        />
      </Card>

      <Card class="flex flex-col gap-5">
        <div class="flex items-center gap-3">
          <Avatar :name="ride.driver_name" :photo-url="ride.driver_photo_url" size="lg" />
          <div class="min-w-0">
            <p class="muted">Conducteur</p>
            <p class="card-title truncate">{{ ride.driver_name }}</p>
            <div class="mt-1 flex flex-wrap items-center gap-2">
              <StarRating v-if="ride.driver_rating_count" :value="Number(ride.driver_rating_average)" readonly show-value size="sm" />
              <TierBadge :tier="{ tier_key: ride.driver_tier_key, tier_label: ride.driver_tier_label }" />
            </div>
          </div>
        </div>

        <dl class="divide-y divide-slate-100 border-y border-slate-100 text-sm">
          <div class="flex items-center justify-between gap-3 py-2.5">
            <dt class="flex items-center gap-2 text-slate-500"><CalendarDays class="h-4 w-4" aria-hidden="true" /> {{ timeLabel }}</dt>
            <dd class="font-semibold text-slate-900">{{ formattedRideTime }}</dd>
          </div>
          <div v-if="ride.passage_time" class="flex items-center justify-between gap-3 py-2.5">
            <dt class="flex items-center gap-2 text-slate-500"><MapPin class="h-4 w-4" aria-hidden="true" /> {{ outbound ? "Dépose" : "Prise en charge" }}</dt>
            <dd class="font-semibold text-slate-900">vers {{ ride.passage_time }}</dd>
          </div>
          <div class="flex items-center justify-between gap-3 py-2.5">
            <dt class="flex items-center gap-2 text-slate-500"><RouteIcon class="h-4 w-4" aria-hidden="true" /> Détour du conducteur</dt>
            <dd class="font-semibold text-slate-900">+{{ formatMinutes(ride.extra_time_min) }}</dd>
          </div>
          <div class="flex items-center justify-between gap-3 py-2.5">
            <dt class="flex items-center gap-2 text-slate-500"><UsersRound class="h-4 w-4" aria-hidden="true" /> Places libres</dt>
            <dd class="font-semibold text-slate-900">{{ availableSeats }}</dd>
          </div>
        </dl>

        <Button block class="mt-auto" :disabled="isConfirming" @click="confirmRide">
          <LoaderCircle v-if="isConfirming" class="h-4 w-4 animate-spin" aria-hidden="true" />
          <Send v-else class="h-4 w-4" aria-hidden="true" />
          {{ isConfirming ? "Envoi..." : "Envoyer la demande" }}
        </Button>
      </Card>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  CalendarDays,
  LoaderCircle,
  MapPin,
  Route as RouteIcon,
  Send,
  UsersRound,
} from "lucide-vue-next";

import RouteMap from "../components/RouteMap.vue";
import { Avatar, Button, Card, DirectionBadge, StarRating, TierBadge } from "../components/ui";
import { isOutbound } from "../lib/direction";
import { formatMinutes, formatShortDateTime } from "../lib/format";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const route = useRoute();
const router = useRouter();

const ride = computed(() => {
  const pending = app.pendingRide;
  return pending && String(pending.ride_id) === String(route.params.rideId) ? pending : null;
});

// Recap perime (onglet rouvert, lien partage) : retour aux resultats.
onMounted(() => {
  if (!ride.value) router.replace("/matches");
});

const isConfirming = computed(
  () => ride.value && String(app.selectionLoadingRideId) === String(ride.value.ride_id),
);
const outbound = computed(() => isOutbound(ride.value?.ride_type));
// L'heure du conducteur est son arrivee a l'aller, son depart au retour.
const timeLabel = computed(() => (outbound.value ? "Arrivée" : "Départ"));
const formattedRideTime = computed(() => formatShortDateTime(String(ride.value?.ride_time || "").replace(" ", "T")));
const availableSeats = computed(() => {
  const value = Number(ride.value?.available_seats ?? ride.value?.car_seats);
  return Number.isFinite(value) ? Math.max(0, value) : 0;
});

async function confirmRide() {
  if (!ride.value || isConfirming.value) return;
  const selected = await app.selectRide(ride.value.ride_id);
  // La demande apparait dans "Mes courses", ou l'on suit la reponse du conducteur.
  if (selected) router.replace("/tracking");
}
</script>

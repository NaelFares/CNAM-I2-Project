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

      <Card class="space-y-4">
        <label v-if="ladiesOnlyAvailable" class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <input v-model="ladiesOnly" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300" />
          <span>
            <span class="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              <Venus class="h-4 w-4 text-pink-600" />
              Covoiturer entre femmes
            </span>
            <span class="mt-0.5 block text-xs text-slate-500">
              Cette recherche ne proposera que des utilisatrices. Votre profil reste visible dans les
              recherches des autres.
            </span>
          </span>
        </label>

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
            <div class="flex items-center gap-2">
              <Avatar :name="match.driver_name" :photo-url="match.driver_photo_url" size="sm" />
              <span class="text-sm font-semibold text-slate-700">
                {{ match.driver_name }} ({{ genderLabel(match.driver_gender) }})
              </span>
              <ArrowRight class="h-4 w-4 shrink-0 text-slate-400" />
              <Avatar :name="match.passenger_name" :photo-url="match.passenger_photo_url" size="sm" />
              <span class="text-sm font-semibold text-slate-700">
                {{ match.passenger_name }} ({{ genderLabel(match.passenger_gender) }})
              </span>
            </div>

            <div class="mt-2 flex flex-wrap gap-1.5">
              <Badge
                v-for="badge in tripPreferenceBadges({
                  music_preference: match.driver_music_preference,
                  smoking_preference: match.driver_smoking_preference,
                })"
                :key="badge"
                variant="info"
              >{{ badge }}</Badge>
              <Badge v-if="match.driver_car_seats" variant="info">
                {{ match.driver_car_seats }} place{{ match.driver_car_seats > 1 ? "s" : "" }}
              </Badge>
            </div>
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
import { computed, onMounted, ref } from "vue";
import { ArrowRight, UsersRound, Venus } from "lucide-vue-next";

import CarpoolResultCard from "../components/CarpoolResultCard.vue";
import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import RouteMap from "../components/RouteMap.vue";
import { Avatar, Badge, Button, Card } from "../components/ui";
import { canUseLadiesOnly, genderLabel } from "../lib/gender";
import { tripPreferenceBadges } from "../lib/preferences";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const activeTab = ref("quick");
const ladiesOnly = ref(false);

const ladiesOnlyAvailable = computed(() => canUseLadiesOnly(app.profile));

onMounted(async () => {
  if (!app.profile) await app.loadProfile();
});

async function runFullPlanningSearch() {
  const ok = await app.generateRides();
  // La case n'est affichee qu'aux utilisatrices, mais on ne se fie pas au
  // rendu : le flag est neutralise si le profil ne le permet pas.
  if (ok) await app.findMatches(ladiesOnlyAvailable.value && ladiesOnly.value);
}
</script>

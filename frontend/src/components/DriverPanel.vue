<template>
  <div class="space-y-5">
    <!-- Pas encore de voiture : une seule question, sans quitter la page -->
    <Card v-if="!hasCar" class="space-y-4">
      <div>
        <h2 class="text-lg font-bold text-slate-900">Combien de places pouvez-vous proposer ?</h2>
        <p class="mt-1 text-sm text-slate-600">
          Sans compter le conducteur. Vous pourrez le changer plus tard dans votre profil.
        </p>
      </div>
      <div class="grid grid-cols-4 gap-2">
        <button
          v-for="count in [1, 2, 3, 4]"
          :key="count"
          type="button"
          class="rounded-xl border border-slate-200 bg-white py-3 text-lg font-bold text-slate-800 transition hover:border-blue-700 hover:bg-blue-50 disabled:opacity-50"
          :disabled="app.loading"
          @click="setSeats(count)"
        >
          {{ count }}
        </button>
      </div>
    </Card>

    <template v-else>
      <!-- Action principale -->
      <OfferRideForm v-if="showForm" @close="showForm = false" @created="showForm = false" />
      <button
        v-else
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-700 px-4 py-4 text-base font-bold text-white shadow-sm transition hover:bg-blue-800"
        @click="showForm = true"
      >
        <Plus class="h-5 w-5" />
        Proposer un trajet
      </button>

      <!-- Mes trajets proposes -->
      <section class="space-y-3">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">Mes trajets proposés</h2>

        <p v-if="app.ridesViewLoading && !app.driverOffers.length" class="text-sm text-slate-500">
          Chargement…
        </p>
        <p v-else-if="!offers.length" class="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          Vous ne proposez aucun trajet pour l'instant.
        </p>

        <Card v-for="ride in offers" :key="ride.id" class="space-y-3">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-base font-bold capitalize text-slate-900">{{ formatDay(ride.ride_time) }}</p>
              <p class="mt-0.5 truncate text-sm text-slate-600">{{ routeLabel(ride) }}</p>
            </div>
            <span
              class="shrink-0 rounded-full px-3 py-1 text-xs font-bold"
              :class="ride.available_seats ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'"
            >
              {{ seatsLabel(ride) }}
            </span>
          </div>

          <!-- Demandes et passagers -->
          <div v-if="visiblePassengers(ride).length" class="space-y-2 border-t border-slate-100 pt-3">
            <div
              v-for="passenger in visiblePassengers(ride)"
              :key="passenger.id"
              class="flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 px-3 py-2"
            >
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-bold text-slate-800">{{ passenger.name }}</p>
                <p
                  class="text-xs font-semibold"
                  :class="passenger.selection_status === 'accepted' ? 'text-emerald-700' : 'text-amber-700'"
                >
                  {{ passenger.selection_status === "accepted" ? "Passager confirmé" : "Demande une place" }}
                </p>
                <p v-if="stopSummary(ride, passenger)" class="text-xs text-slate-500">
                  {{ stopSummary(ride, passenger) }}
                </p>
              </div>
              <Button
                v-if="passenger.selection_status === 'pending'"
                :disabled="busy(ride)"
                @click="app.decidePassenger(ride.id, passenger.id, 'accept')"
              >
                <Check class="h-4 w-4" />
                Accepter
              </Button>
              <Button
                variant="secondary"
                :disabled="busy(ride)"
                @click="app.decidePassenger(ride.id, passenger.id, 'reject')"
              >
                {{ passenger.selection_status === "accepted" ? "Retirer" : "Refuser" }}
              </Button>
            </div>
          </div>
          <p v-else class="border-t border-slate-100 pt-3 text-sm text-slate-500">
            Personne n'a encore demandé de place.
          </p>

          <div class="flex flex-wrap items-center justify-end gap-2">
            <p v-if="visiblePassengers(ride).length" class="mr-auto text-xs text-slate-500">
              Pour annuler, refusez d'abord les demandes et passagers.
            </p>
            <Button
              variant="secondary"
              :disabled="busy(ride) || visiblePassengers(ride).length > 0"
              @click="app.withdrawOffer(ride.id)"
            >
              <X class="h-4 w-4" />
              Annuler ce trajet
            </Button>
          </div>
        </Card>
      </section>

      <!-- Suggestions depuis l'emploi du temps -->
      <section class="space-y-3">
        <div>
          <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">Depuis mon emploi du temps</h2>
          <p class="text-xs text-slate-500">Vos trajets de cours : proposez ceux où vous prenez la voiture.</p>
        </div>

        <template v-if="suggestions.length">
          <div
            v-for="ride in shownSuggestions"
            :key="ride.id"
            class="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5"
          >
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold capitalize text-slate-800">{{ formatDay(ride.ride_time) }}</p>
              <p class="truncate text-xs text-slate-500">{{ routeLabel(ride) }}</p>
            </div>
            <Button variant="secondary" :disabled="busy(ride)" @click="app.toggleRideOffer(ride.id, true)">
              <Plus class="h-4 w-4" />
              Proposer
            </Button>
          </div>
          <button
            v-if="suggestions.length > shownSuggestions.length"
            type="button"
            class="text-sm font-semibold text-blue-700 hover:underline"
            @click="showAllSuggestions = true"
          >
            Voir les {{ suggestions.length - shownSuggestions.length }} autres trajets
          </button>
        </template>

        <div v-else-if="!hasTimetableRides" class="space-y-3 rounded-xl border border-dashed border-slate-300 p-4">
          <p class="text-sm text-slate-600">
            Importez votre emploi du temps pour retrouver ici vos trajets de cours, prêts à proposer.
          </p>
          <div class="flex flex-wrap gap-2">
            <RouterLink to="/schedule">
              <Button variant="secondary">
                <CalendarDays class="h-4 w-4" />
                Importer mon emploi du temps
              </Button>
            </RouterLink>
            <!-- Planning deja importe mais trajets jamais generes -->
            <Button variant="secondary" :disabled="app.loading" @click="generateFromTimetable">
              Créer mes trajets de cours
            </Button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">Tous vos trajets de cours à venir sont déjà proposés.</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { CalendarDays, Check, Plus, X } from "lucide-vue-next";

import OfferRideForm from "./OfferRideForm.vue";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";
import { Button, Card } from "./ui";

const app = useAppStore();
const auth = useAuthStore();

const showForm = ref(false);
const showAllSuggestions = ref(false);
const SUGGESTION_LIMIT = 4;

// Le profil fait foi apres une sauvegarde ; auth.user sert de repli.
const hasCar = computed(() => Boolean((app.profile ?? auth.user)?.car_seats));

const upcoming = computed(() =>
  [...app.driverOffers]
    .filter((ride) => new Date(ride.ride_time) > new Date())
    .sort((a, b) => String(a.ride_time).localeCompare(String(b.ride_time)))
);
const offers = computed(() => upcoming.value.filter((ride) => ride.is_offer));
// Suggestions : trajets de l'emploi du temps (event_id) pas encore proposes.
const suggestions = computed(() => upcoming.value.filter((ride) => !ride.is_offer && ride.event_id));
const shownSuggestions = computed(() =>
  showAllSuggestions.value ? suggestions.value : suggestions.value.slice(0, SUGGESTION_LIMIT)
);
const hasTimetableRides = computed(() => app.driverOffers.some((ride) => ride.event_id));

function busy(ride) {
  return String(app.selectionLoadingRideId) === String(ride.id);
}

// Les demandes refusees n'ont plus d'interet pour le conducteur.
function visiblePassengers(ride) {
  return ride.passengers.filter((passenger) => passenger.selection_status !== "rejected");
}

// Ce que le conducteur doit savoir avant d'accepter : ou et quand il passe,
// et ce que ca lui coute. Vide pour les demandes plus anciennes.
function stopSummary(ride, passenger) {
  const parts = [];
  if (passenger.passage_time) {
    parts.push(`${ride.ride_type === "to_campus" ? "Dépose" : "Prise en charge"} vers ${passenger.passage_time}`);
  }
  if (passenger.pickup_on_the_way) parts.push("monte en chemin");
  if (passenger.dropoff_on_the_way) parts.push("descend en chemin");
  if (passenger.detour_min != null) parts.push(`+${Number(passenger.detour_min).toFixed(1)} min de détour`);
  return parts.join(" · ");
}

function seatsLabel(ride) {
  const free = ride.available_seats;
  if (!free) return "Complet";
  const plural = free > 1 ? "s" : "";
  return `${free} place${plural} libre${plural} sur ${ride.car_seats}`;
}

function formatDay(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const day = date.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
  const hour = date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  return `${day} · ${hour}`;
}

// Premiere partie d'une adresse : "12 Rue de Metz, 31000 Toulouse" -> "12 Rue de Metz".
function shortAddress(address) {
  return String(address || "").split(",")[0].trim();
}

function routeLabel(ride) {
  if (ride.start_address || ride.end_address) {
    return `${shortAddress(ride.start_address) || "Départ"} → ${shortAddress(ride.end_address) || "Arrivée"}`;
  }
  // Trajet de l'emploi du temps : du domicile a l'ecole du profil.
  return ride.ride_type === "to_campus" ? "Domicile → École" : "École → Domicile";
}

async function setSeats(count) {
  const p = app.profile;
  if (!p) return;
  await app.saveProfile({
    name: p.name,
    email: p.email,
    gender: p.gender,
    music_preference: p.music_preference,
    music_genres: p.music_genres || [],
    smoking_preference: p.smoking_preference,
    car_seats: count,
    start_address: p.start_address,
    start_lat: p.start_lat,
    start_lon: p.start_lon,
    time_tolerance_min: p.time_tolerance_min,
    school_address: p.school_address,
    school_lat: p.school_lat,
    school_lon: p.school_lon,
  });
}

async function generateFromTimetable() {
  const ok = await app.generateRides();
  if (ok) await app.loadDriverOffers();
}

onMounted(async () => {
  if (!app.profile) await app.loadProfile();
  await app.loadDriverOffers();
});
</script>

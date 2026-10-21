<template>
  <div class="space-y-8">
    <!-- Pas encore de voiture : une seule question, sans quitter la page -->
    <Card v-if="!hasCar" class="space-y-4">
      <div>
        <h2 class="section-title">Combien de places pouvez-vous proposer ?</h2>
        <p class="muted mt-1">Sans compter le conducteur. Modifiable ensuite dans votre profil.</p>
      </div>
      <div class="grid grid-cols-4 gap-2">
        <button
          v-for="count in [1, 2, 3, 4]"
          :key="count"
          type="button"
          class="rounded-xl border border-slate-200 bg-white py-3 text-lg font-bold text-slate-800 transition hover:border-primary hover:bg-primary-soft disabled:opacity-50"
          :disabled="app.loading"
          @click="setSeats(count)"
        >
          {{ count }}
        </button>
      </div>
    </Card>

    <template v-else>
      <OfferRideForm v-if="showForm" @close="showForm = false" @created="showForm = false" />

      <!-- 1. Ce qui attend une reponse, en premier -->
      <section v-if="pendingRequests.length" class="space-y-3">
        <SectionHeader title="Demandes à traiter" :count="pendingRequests.length">
          <template #icon><BellRing class="h-5 w-5 text-warning" aria-hidden="true" /></template>
        </SectionHeader>
        <ShowMore :items="pendingRequests" :limit="4" item-key="key">
          <template #default="{ item: request }">
            <Card padding="p-4" class="flex flex-wrap items-center gap-3">
              <Avatar :name="request.passenger.name" size="md" />
              <div class="min-w-0 flex-1">
                <p class="card-title truncate">{{ request.passenger.name }}</p>
                <div class="mt-1 flex flex-wrap items-center gap-2 text-[0.8125rem] text-slate-600">
                  <DirectionBadge :ride-type="request.ride.ride_type" />
                  <span>{{ formatShortDateTime(request.ride.ride_time) }}</span>
                </div>
                <StopDetails :ride="request.ride" :passenger="request.passenger" class="mt-1" />
              </div>
              <div class="flex gap-2">
                <Button size="sm" :disabled="busy(request.ride)" @click="app.decidePassenger(request.ride.id, request.passenger.id, 'accept')">
                  <Check class="h-4 w-4" aria-hidden="true" />
                  Accepter
                </Button>
                <Button size="sm" variant="secondary" :disabled="busy(request.ride)" @click="app.decidePassenger(request.ride.id, request.passenger.id, 'reject')">
                  Refuser
                </Button>
              </div>
            </Card>
          </template>
        </ShowMore>
      </section>

      <!-- 2. Mes trajets proposes, semaine par semaine -->
      <section class="space-y-3">
        <SectionHeader title="Mes trajets proposés" :count="offers.length || null">
          <template #action>
            <Button v-if="!showForm" size="sm" @click="showForm = true">
              <Plus class="h-4 w-4" aria-hidden="true" />
              Proposer un trajet
            </Button>
          </template>
        </SectionHeader>

        <p v-if="app.ridesViewLoading && !app.driverOffers.length" class="muted">Chargement…</p>
        <EmptyState
          v-else-if="!offers.length"
          :icon="CarFront"
          title="Aucun trajet proposé"
          text="Proposez un trajet, ou partez de votre emploi du temps ci-dessous."
        />
        <Card v-else>
          <WeekCalendar :monday="week" :items="calendarItems" @navigate="moveWeek">
            <template #item="{ item }">
              <button
                type="button"
                class="calendar-chip"
                :class="[item.outbound ? 'calendar-chip--out' : 'calendar-chip--back', { 'is-selected': selectedRideId === item.ride.id }]"
                @click="selectedRideId = item.ride.id"
              >
                <span class="flex items-center justify-between gap-1">
                  <span class="font-semibold text-slate-900">{{ item.time }}</span>
                  <span
                    v-if="pendingCount(item.ride)"
                    class="h-2 w-2 rounded-full bg-warning"
                    :title="`${pendingCount(item.ride)} demande(s) en attente`"
                  ></span>
                </span>
                <span class="flex items-center gap-1 text-xs text-slate-500">
                  <UsersRound class="h-3.5 w-3.5" aria-hidden="true" />
                  {{ acceptedCount(item.ride) }}/{{ item.ride.car_seats }}
                </span>
              </button>
            </template>
          </WeekCalendar>
        </Card>
      </section>

      <!-- 3. Suggestions depuis l'emploi du temps -->
      <section class="space-y-3">
        <SectionHeader title="Depuis mon emploi du temps" subtitle="Vos trajets de cours : proposez ceux où vous prenez la voiture." />

        <ShowMore v-if="suggestions.length" :items="suggestions" :limit="4" item-key="id" list-class="grid gap-2 md:grid-cols-2">
          <template #default="{ item: ride }">
            <div class="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5">
              <DirectionBadge :ride-type="ride.ride_type" />
              <span class="min-w-0 flex-1 truncate text-sm text-slate-700">{{ formatShortDateTime(ride.ride_time) }}</span>
              <Button size="sm" variant="secondary" :disabled="busy(ride)" @click="app.toggleRideOffer(ride.id, true)">
                <Plus class="h-4 w-4" aria-hidden="true" />
                Proposer
              </Button>
            </div>
          </template>
        </ShowMore>

        <EmptyState
          v-else-if="!hasTimetableRides"
          :icon="CalendarDays"
          title="Pas encore d'emploi du temps"
          text="Importez-le pour retrouver ici vos trajets de cours, prêts à proposer."
        >
          <div class="flex flex-wrap justify-center gap-2">
            <RouterLink to="/schedule" class="btn-primary btn-sm">
              <CalendarDays class="h-4 w-4" aria-hidden="true" />
              Importer mon planning
            </RouterLink>
            <!-- Planning deja importe mais trajets jamais generes -->
            <Button size="sm" variant="secondary" :disabled="app.loading" @click="generateFromTimetable">
              Créer mes trajets de cours
            </Button>
          </div>
        </EmptyState>
        <p v-else class="muted flex items-center gap-2">
          <CircleCheck class="h-4 w-4 text-success" aria-hidden="true" />
          Tous vos trajets de cours à venir sont déjà proposés.
        </p>
      </section>
    </template>

    <!-- Detail d'un trajet propose -->
    <SidePanel
      :open="Boolean(selectedRide)"
      :title="selectedRide ? formatShortDateTime(selectedRide.ride_time) : 'Trajet'"
      @close="selectedRideId = null"
    >
      <template #subtitle>
        <div v-if="selectedRide" class="mt-1 flex flex-wrap items-center gap-2">
          <DirectionBadge :ride-type="selectedRide.ride_type" />
          <span class="muted inline-flex items-center gap-1">
            {{ routeEnds(selectedRide)[0] }}
            <ArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
            {{ routeEnds(selectedRide)[1] }}
          </span>
        </div>
      </template>

      <template v-if="selectedRide">
        <p class="mb-3 text-sm font-semibold" :class="selectedRide.available_seats ? 'text-success' : 'text-slate-500'">
          {{ seatsLabel(selectedRide) }}
        </p>
        <ul v-if="visiblePassengers(selectedRide).length" class="divide-y divide-slate-100">
          <li v-for="passenger in visiblePassengers(selectedRide)" :key="passenger.id" class="flex items-start gap-3 py-3">
            <Avatar :name="passenger.name" size="md" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="truncate font-semibold text-slate-900">{{ passenger.name }}</p>
                <Badge :variant="passenger.selection_status === 'accepted' ? 'success' : 'warning'">
                  {{ passenger.selection_status === "accepted" ? "Confirmé" : "En attente" }}
                </Badge>
              </div>
              <StopDetails :ride="selectedRide" :passenger="passenger" class="mt-1.5" />
              <div class="mt-2 flex gap-2">
                <Button
                  v-if="passenger.selection_status === 'pending'"
                  size="sm"
                  :disabled="busy(selectedRide)"
                  @click="app.decidePassenger(selectedRide.id, passenger.id, 'accept')"
                >
                  <Check class="h-4 w-4" aria-hidden="true" />
                  Accepter
                </Button>
                <Button size="sm" variant="secondary" :disabled="busy(selectedRide)" @click="app.decidePassenger(selectedRide.id, passenger.id, 'reject')">
                  {{ passenger.selection_status === "accepted" ? "Retirer" : "Refuser" }}
                </Button>
              </div>
            </div>
          </li>
        </ul>
        <p v-else class="muted">Personne n'a encore demandé de place.</p>
      </template>

      <template #footer>
        <div v-if="selectedRide" class="flex flex-col gap-2">
          <Button
            variant="danger"
            block
            :disabled="busy(selectedRide) || visiblePassengers(selectedRide).length > 0"
            @click="withdraw(selectedRide)"
          >
            <X class="h-4 w-4" aria-hidden="true" />
            Annuler ce trajet
          </Button>
          <p v-if="visiblePassengers(selectedRide).length" class="muted text-center">
            Refusez d'abord les demandes et passagers.
          </p>
        </div>
      </template>
    </SidePanel>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import {
  ArrowRight,
  BellRing,
  CalendarDays,
  CarFront,
  Check,
  CircleCheck,
  Plus,
  UsersRound,
  X,
} from "lucide-vue-next";

import OfferRideForm from "./OfferRideForm.vue";
import StopDetails from "./StopDetails.vue";
import WeekCalendar from "./WeekCalendar.vue";
import { isOutbound } from "../lib/direction";
import { formatShortDateTime, formatTime } from "../lib/format";
import { localDateIso, mondayIso, shiftWeek } from "../lib/week";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";
import {
  Avatar,
  Badge,
  Button,
  Card,
  DirectionBadge,
  EmptyState,
  SectionHeader,
  ShowMore,
  SidePanel,
} from "./ui";

const app = useAppStore();
const auth = useAuthStore();

const showForm = ref(false);
const selectedRideId = ref(null);
const week = ref(mondayIso(localDateIso()));

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
const hasTimetableRides = computed(() => app.driverOffers.some((ride) => ride.event_id));

const pendingRequests = computed(() =>
  offers.value.flatMap((ride) =>
    ride.passengers
      .filter((passenger) => passenger.selection_status === "pending")
      .map((passenger) => ({ key: `${ride.id}-${passenger.id}`, ride, passenger })),
  ),
);

const calendarItems = computed(() =>
  offers.value.map((ride) => ({
    key: ride.id,
    date: localIso(ride.ride_time),
    outbound: isOutbound(ride.ride_type),
    time: formatTime(ride.ride_time),
    ride,
  })),
);

// Le detail suit les donnees rechargees apres chaque decision.
const selectedRide = computed(() => offers.value.find((ride) => ride.id === selectedRideId.value) || null);

// Le calendrier s'ouvre sur la semaine du prochain trajet propose.
// Watch plutot qu'au montage : les offres peuvent arriver apres coup.
let weekInitialised = false;
watch(
  () => offers.value[0],
  (first) => {
    if (weekInitialised || !first) return;
    weekInitialised = true;
    week.value = mondayIso(localIso(first.ride_time).slice(0, 10));
  },
  { immediate: true },
);

function moveWeek(offset) {
  week.value = offset === 0 ? mondayIso(localDateIso()) : shiftWeek(week.value, offset);
}

function localIso(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : `${localDateIso(date)}T${formatTime(date)}`;
}

function busy(ride) {
  return String(app.selectionLoadingRideId) === String(ride.id);
}

// Les demandes refusees n'ont plus d'interet pour le conducteur.
function visiblePassengers(ride) {
  return ride.passengers.filter((passenger) => passenger.selection_status !== "rejected");
}

function pendingCount(ride) {
  return ride.passengers.filter((passenger) => passenger.selection_status === "pending").length;
}

function acceptedCount(ride) {
  return ride.passengers.filter((passenger) => passenger.selection_status === "accepted").length;
}

function seatsLabel(ride) {
  const free = ride.available_seats;
  if (!free) return "Complet";
  const plural = free > 1 ? "s" : "";
  return `${free} place${plural} libre${plural} sur ${ride.car_seats}`;
}

// Premiere partie d'une adresse : "12 Rue de Metz, 31000 Toulouse" -> "12 Rue de Metz".
function shortAddress(address) {
  return String(address || "").split(",")[0].trim();
}

function routeEnds(ride) {
  if (ride.start_address || ride.end_address) {
    return [shortAddress(ride.start_address) || "Départ", shortAddress(ride.end_address) || "Arrivée"];
  }
  // Trajet de l'emploi du temps : du domicile a l'ecole du profil.
  return isOutbound(ride.ride_type) ? ["Domicile", "École"] : ["École", "Domicile"];
}

async function withdraw(ride) {
  await app.withdrawOffer(ride.id);
  selectedRideId.value = null;
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
  // Toujours recharger : un profil en memoire peut etre perime.
  await app.loadProfile();
  await app.loadDriverOffers();
});
</script>

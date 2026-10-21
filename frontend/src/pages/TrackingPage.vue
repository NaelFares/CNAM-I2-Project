<template>
  <section class="page-shell">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div class="page-header">
        <h1 class="page-title">Mes courses</h1>
        <p class="page-subtitle">Vos courses du jour, vos demandes et votre semaine.</p>
      </div>
      <!-- Meme profil, deux roles : on peut n'afficher que l'un des deux -->
      <div class="segmented" role="tablist" aria-label="Filtrer par rôle">
        <button v-for="option in ROLE_FILTERS" :key="option.value" type="button" role="tab" :aria-selected="roleFilter === option.value" @click="roleFilter = option.value">
          <component :is="option.icon" v-if="option.icon" class="h-4 w-4" aria-hidden="true" />
          {{ option.label }}
        </button>
      </div>
    </header>

    <p v-if="!store.loaded && store.loading" class="muted">Chargement de vos courses…</p>

    <template v-else>
      <!-- 1. En cours : chaque etape se confirme des deux cotes -->
      <section class="space-y-3">
        <SectionHeader title="En cours" :count="active.length || null" subtitle="Chaque étape se confirme des deux côtés." />
        <div v-if="active.length" class="grid gap-4 lg:grid-cols-2">
          <TrackingCard v-for="tracking in active" :key="tracking.id" :tracking="tracking" />
        </div>
        <EmptyState
          v-else
          :icon="CarFront"
          title="Aucune course aujourd'hui"
          :text="emptyText"
        >
          <RouterLink v-if="!upcoming.length && roleFilter !== 'driver'" to="/matches" class="btn-primary btn-sm">
            <Search class="h-4 w-4" aria-hidden="true" />
            Trouver un covoiturage
          </RouterLink>
          <RouterLink v-if="!upcoming.length && roleFilter !== 'passenger'" to="/matches?mode=drive" class="btn-secondary btn-sm">
            <CarFront class="h-4 w-4" aria-hidden="true" />
            {{ waitingOffers ? "Voir mes trajets proposés" : "Proposer un trajet" }}
          </RouterLink>
        </EmptyState>
      </section>

      <!-- 2. Demandes envoyees, en attente de la reponse du conducteur -->
      <section v-if="openRequests.length && roleFilter !== 'driver'" class="space-y-3">
        <SectionHeader title="Demandes envoyées" :count="openRequests.length" subtitle="Comme passager. Une demande acceptée devient une course." />
        <ShowMore :items="openRequests" :limit="4" item-key="selection_id" list-class="grid gap-3 md:grid-cols-2">
          <template #default="{ item: request }">
            <Card padding="p-4" class="flex items-center gap-3">
              <Avatar :name="request.driver_name" size="md" />
              <div class="min-w-0 flex-1">
                <p class="card-title truncate">{{ request.driver_name }}</p>
                <div class="mt-1 flex flex-wrap items-center gap-2 text-[0.8125rem] text-slate-600">
                  <DirectionBadge :ride-type="request.ride_type" />
                  <span>{{ formatShortDateTime(request.ride_time) }}</span>
                </div>
                <Badge :variant="request.selection_status === 'rejected' ? 'danger' : 'warning'" class="mt-2">
                  {{ request.selection_status === "rejected" ? "Refusée" : "En attente" }}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                :disabled="String(app.selectionLoadingRideId) === String(request.ride_id)"
                :aria-label="request.selection_status === 'rejected' ? 'Retirer la demande' : 'Annuler la demande'"
                @click="app.cancelRideSelection(request.ride_id)"
              >
                <X class="h-4 w-4" aria-hidden="true" />
                {{ request.selection_status === "rejected" ? "Retirer" : "Annuler" }}
              </Button>
            </Card>
          </template>
        </ShowMore>
      </section>

      <!-- 3. A venir : la semaine en calendrier -->
      <section v-if="upcoming.length" class="space-y-3">
        <SectionHeader title="À venir" :count="upcoming.length" />
        <Card>
          <WeekCalendar :monday="week" :items="calendarItems" @navigate="moveWeek">
            <template #item="{ item }">
              <button
                type="button"
                class="calendar-chip"
                :class="item.outbound ? 'calendar-chip--out' : 'calendar-chip--back'"
                @click="selectedId = item.tracking.id"
              >
                <span class="font-semibold text-slate-900">{{ item.time }}</span>
                <span class="flex min-w-0 items-center gap-1 text-xs text-slate-500">
                  <component :is="item.tracking.my_role === 'driver' ? CarFront : UserRound" class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span class="truncate">{{ item.tracking.counterpart_name }}</span>
                </span>
              </button>
            </template>
          </WeekCalendar>
          <p class="muted mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
            <span class="inline-flex items-center gap-1"><CarFront class="h-3.5 w-3.5" aria-hidden="true" /> Vous conduisez</span>
            <span class="inline-flex items-center gap-1"><UserRound class="h-3.5 w-3.5" aria-hidden="true" /> Vous êtes passager</span>
          </p>
        </Card>
      </section>

      <!-- 4. Historique, le plus recent d'abord -->
      <section v-if="finished.length" class="space-y-3">
        <SectionHeader title="Historique" :count="finished.length" />
        <ShowMore :items="finished" :limit="4" item-key="id" list-class="grid gap-4 lg:grid-cols-2">
          <template #default="{ item: tracking }">
            <TrackingCard :tracking="tracking" compact />
          </template>
        </ShowMore>
      </section>
    </template>

    <!-- Detail d'une course a venir -->
    <SidePanel :open="Boolean(selected)" title="Course à venir" @close="selectedId = null">
      <TrackingCard v-if="selected" :tracking="selected" compact class="border-0 p-0 shadow-none" />
    </SidePanel>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { CarFront, Search, UserRound, X } from "lucide-vue-next";

import TrackingCard from "../components/TrackingCard.vue";
import WeekCalendar from "../components/WeekCalendar.vue";
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
} from "../components/ui";
import { isOutbound } from "../lib/direction";
import { formatShortDateTime, formatTime } from "../lib/format";
import { localDateIso, mondayIso, shiftWeek } from "../lib/week";
import { useAppStore } from "../stores/app";
import { useTrackingStore } from "../stores/tracking";

const ROLE_FILTERS = [
  { value: "all", label: "Tout" },
  { value: "passenger", label: "Passager", icon: UserRound },
  { value: "driver", label: "Conducteur", icon: CarFront },
];

const store = useTrackingStore();
const app = useAppStore();

// Les demandes acceptees ont leur course (en cours ou a venir) : seules
// restent ici celles en attente ou refusees.
const openRequests = computed(() =>
  app.mySelections.filter((request) => request.selection_status !== "accepted")
);

const roleFilter = ref("all");
const byRole = (list) => (roleFilter.value === "all" ? list : list.filter((t) => t.my_role === roleFilter.value));
const active = computed(() => byRole(store.active));
const upcoming = computed(() => byRole(store.upcoming));
const finished = computed(() => byRole(store.finished));

// Un trajet propose ne devient une course qu'avec un passager accepte :
// avant, il reste dans Covoiturage > Proposer.
const waitingOffers = computed(
  () =>
    app.driverOffers.filter(
      (ride) =>
        ride.is_offer &&
        new Date(ride.ride_time) > new Date() &&
        !ride.passengers.some((p) => p.selection_status === "accepted"),
    ).length,
);
const emptyText = computed(() => {
  if (upcoming.value.length) return "Vos prochaines courses sont dans le calendrier ci-dessous.";
  if (roleFilter.value !== "passenger" && waitingOffers.value)
    return `${waitingOffers.value} trajet${waitingOffers.value > 1 ? "s" : ""} proposé${waitingOffers.value > 1 ? "s" : ""} sans passager accepté pour l'instant.`;
  if (roleFilter.value === "driver") return "Proposez votre voiture depuis Covoiturage.";
  if (roleFilter.value === "passenger") return "Réservez une place depuis Covoiturage.";
  return "Réservez une place ou proposez votre voiture depuis Covoiturage.";
});

const week = ref(mondayIso(localDateIso()));
const selectedId = ref(null);
const selected = computed(() => upcoming.value.find((tracking) => tracking.id === selectedId.value) || null);

const calendarItems = computed(() =>
  upcoming.value.map((tracking) => {
    const date = new Date(tracking.ride_time);
    return {
      key: tracking.id,
      date: `${localDateIso(date)}T${formatTime(date)}`,
      outbound: isOutbound(tracking.ride_type),
      time: formatTime(date),
      tracking,
    };
  }),
);

function moveWeek(offset) {
  week.value = offset === 0 ? mondayIso(localDateIso()) : shiftWeek(week.value, offset);
}

// Le calendrier s'ouvre sur la semaine de la prochaine course.
let weekChosen = false;
watch(
  () => store.upcoming[0],
  (first) => {
    if (weekChosen || !first) return;
    weekChosen = true;
    week.value = mondayIso(localDateIso(new Date(first.ride_time)));
  },
  { immediate: true },
);

onMounted(() => {
  store.load();
  app.loadMySelections();
  app.loadDriverOffers();
});
</script>

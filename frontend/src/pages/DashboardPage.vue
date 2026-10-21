<template>
  <section class="page-shell !space-y-5">
    <header class="page-header">
      <h1 class="page-title">Bonjour {{ firstName }}</h1>
      <p class="page-subtitle">Voici ce qui vous attend.</p>
    </header>

    <!-- Ce qui compte maintenant : la prochaine course et ce qui attend une reponse -->
    <div class="grid items-start gap-4 md:grid-cols-3">
      <RouterLink to="/tracking" class="card group flex flex-col gap-3 p-4 transition hover:border-slate-300 md:col-span-2">
        <div class="flex items-center justify-between">
          <p class="muted font-semibold">Prochaine course</p>
          <ChevronRight class="h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5" aria-hidden="true" />
        </div>
        <div v-if="nextRide" class="flex items-center gap-3">
          <Avatar :name="nextRide.counterpart_name" :photo-url="nextRide.counterpart_photo_url" size="lg" />
          <div class="min-w-0">
            <p class="text-lg font-semibold text-slate-900">{{ formatShortDateTime(nextRide.ride_time) }}</p>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-600">
              <RoleBadge :role="nextRide.my_role" />
              <DirectionBadge :ride-type="nextRide.ride_type" />
              <span>avec {{ nextRide.counterpart_name }}</span>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-slate-600">Aucune course prévue. Cherchez une place ou proposez votre voiture.</p>
      </RouterLink>

      <div class="grid gap-4">
        <RouterLink to="/matches?mode=drive" class="card group flex items-center gap-3 p-4 transition hover:border-slate-300">
          <span class="grid h-10 w-10 place-items-center rounded-full" :class="driverRequests ? 'bg-warning-soft text-warning' : 'bg-slate-100 text-slate-400'">
            <BellRing class="h-5 w-5" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-2xl font-bold text-slate-900">{{ driverRequests }}</p>
            <p class="muted">demande{{ driverRequests > 1 ? "s" : "" }} à traiter</p>
            <RoleBadge role="driver" class="mt-1" />
          </div>
          <ChevronRight class="h-4 w-4 text-slate-400" aria-hidden="true" />
        </RouterLink>
        <RouterLink to="/tracking" class="card group flex items-center gap-3 p-4 transition hover:border-slate-300">
          <span class="grid h-10 w-10 place-items-center rounded-full bg-slate-100 text-slate-500">
            <Send class="h-5 w-5" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-2xl font-bold text-slate-900">{{ sentRequests }}</p>
            <p class="muted">demande{{ sentRequests > 1 ? "s" : "" }} envoyée{{ sentRequests > 1 ? "s" : "" }}</p>
            <RoleBadge role="passenger" class="mt-1" />
          </div>
          <ChevronRight class="h-4 w-4 text-slate-400" aria-hidden="true" />
        </RouterLink>
      </div>
    </div>

    <!-- Premiers pas : visible tant que le compte n'est pas pret -->
    <Card v-if="onboarding.some((step) => !step.done)" class="space-y-3">
      <SectionHeader title="Pour bien démarrer" :subtitle="`${onboarding.filter((step) => step.done).length} sur ${onboarding.length} étapes faites`" />
      <ul class="divide-y divide-slate-100">
        <li v-for="step in onboarding" :key="step.to">
          <RouterLink :to="step.to" class="flex items-center gap-3 py-2.5 text-sm">
            <CircleCheck v-if="step.done" class="h-5 w-5 text-success" aria-hidden="true" />
            <Circle v-else class="h-5 w-5 text-slate-300" aria-hidden="true" />
            <span :class="step.done ? 'text-slate-400 line-through' : 'font-medium text-slate-800'">{{ step.label }}</span>
            <ChevronRight v-if="!step.done" class="ml-auto h-4 w-4 text-slate-400" aria-hidden="true" />
          </RouterLink>
        </li>
      </ul>
    </Card>

    <section class="space-y-3">
      <SectionHeader title="Raccourcis" />
      <div class="grid items-start gap-4 md:grid-cols-3">
        <RouterLink v-for="shortcut in shortcuts" :key="shortcut.to" :to="shortcut.to" class="card group p-4 transition hover:border-slate-300">
          <StepAnimation :variant="shortcut.animation" class="mb-3 h-24 w-full" />
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="card-title">{{ shortcut.title }}</h3>
              <p class="muted mt-1">{{ shortcut.text }}</p>
            </div>
            <ArrowRight class="h-5 w-5 shrink-0 text-primary transition group-hover:translate-x-1" aria-hidden="true" />
          </div>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import {
  ArrowRight,
  BellRing,
  ChevronRight,
  Circle,
  CircleCheck,
  Send,
} from "lucide-vue-next";

import StepAnimation from "../components/StepAnimation.vue";
import { Avatar, Card, DirectionBadge, RoleBadge, SectionHeader } from "../components/ui";
import { formatShortDateTime } from "../lib/format";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";
import { useTrackingStore } from "../stores/tracking";

const app = useAppStore();
const auth = useAuthStore();
const tracking = useTrackingStore();

const firstName = computed(() => String(auth.user?.name || "").split(" ")[0] || "et bienvenue");

// Course la plus proche : en cours d'abord, sinon la prochaine a venir.
const nextRide = computed(() => tracking.active[0] || tracking.upcoming[0] || null);

const driverRequests = computed(() =>
  app.driverOffers
    .filter((ride) => ride.is_offer && new Date(ride.ride_time) > new Date())
    .reduce((total, ride) => total + ride.passengers.filter((p) => p.selection_status === "pending").length, 0),
);
const sentRequests = computed(() => app.mySelections.filter((request) => request.selection_status === "pending").length);

const onboarding = computed(() => [
  { to: "/profile", label: "Renseigner mon domicile et mon école", done: Boolean(app.summary?.profile_completed) },
  { to: "/schedule", label: "Importer mon emploi du temps", done: Boolean(app.summary?.events_count) },
  { to: "/matches", label: "Chercher ou proposer un premier trajet", done: Boolean(nextRide.value || sentRequests.value) },
]);

const shortcuts = [
  { to: "/schedule", animation: "import", title: "Mon planning", text: "Importer ou consulter vos cours." },
  { to: "/profile", animation: "profile", title: "Mon profil", text: "Adresses, voiture et préférences." },
  { to: "/matches", animation: "carpool", title: "Covoiturage", text: "Chercher une place ou proposer la vôtre." },
];

onMounted(() => {
  app.loadSummary();
  tracking.load();
  app.loadDriverOffers();
  app.loadMySelections();
});
</script>

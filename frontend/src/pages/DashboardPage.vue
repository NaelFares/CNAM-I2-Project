<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Tableau de bord</h1>
      <p class="page-subtitle">Bonjour {{ displayName }}, suivez votre avancement et lancez rapidement les etapes importantes.</p>
    </header>

    <div class="grid gap-4 md:grid-cols-3">
      <article class="card p-5">
        <div class="flex items-center justify-between">
          <p class="text-sm font-semibold text-slate-500">Cours importes</p>
          <CalendarDays class="h-5 w-5 text-blue-700" />
        </div>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ app.summary?.events_count ?? 0 }}</p>
      </article>

      <article class="card p-5">
        <div class="flex items-center justify-between">
          <p class="text-sm font-semibold text-slate-500">Trajets generes</p>
          <Route class="h-5 w-5 text-blue-700" />
        </div>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ app.summary?.rides_count ?? 0 }}</p>
      </article>

      <article class="card p-5">
        <div class="flex items-center justify-between">
          <p class="text-sm font-semibold text-slate-500">Profil complete</p>
          <CircleCheckBig class="h-5 w-5" :class="app.summary?.profile_completed ? 'text-emerald-600' : 'text-amber-600'" />
        </div>
        <p class="mt-2 text-3xl font-bold" :class="app.summary?.profile_completed ? 'text-emerald-700' : 'text-amber-700'">
          {{ app.summary?.profile_completed ? "Oui" : "Non" }}
        </p>
      </article>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <RouterLink to="/schedule" class="card group p-5 transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-strong)]">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Importer mon planning</h2>
            <p class="mt-1 text-sm text-slate-600">Chargez un fichier ICS ou CSV.</p>
          </div>
          <ArrowRight class="h-5 w-5 text-blue-700 transition group-hover:translate-x-1" />
        </div>
      </RouterLink>

      <RouterLink to="/profile" class="card group p-5 transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-strong)]">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Completer mon profil</h2>
            <p class="mt-1 text-sm text-slate-600">Adresse, role et tolerance horaire.</p>
          </div>
          <ArrowRight class="h-5 w-5 text-blue-700 transition group-hover:translate-x-1" />
        </div>
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { ArrowRight, CalendarDays, CircleCheckBig, Route } from "lucide-vue-next";

import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";

const app = useAppStore();
const auth = useAuthStore();
const displayName = computed(() => auth.user?.name || "etudiant");

onMounted(async () => {
  await app.loadSummary();
});
</script>

<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mes trajets</h1>
      <p class="page-subtitle">Générez vos trajets à partir des cours importés.</p>
    </header>

    <div class="advice-banner">Conseil: regénérez les trajets après toute modification majeure de planning.</div>

    <div class="card p-6">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm font-medium text-slate-600">Opération automatique basée sur vos cours validés.</p>
        <button class="btn-primary" :disabled="app.loading" @click="app.generateRides">
          <Route class="h-4 w-4" />
          Générer mes trajets
        </button>
      </div>
    </div>

    <div v-if="app.rides.length" class="card p-6">
      <h2 class="mb-2 text-xl font-bold text-slate-900">{{ app.rides.length }} trajets générés</h2>
      <p class="text-sm text-slate-600">Vous pouvez maintenant lancer la recherche de correspondances.</p>
    </div>
  </section>
</template>

<script setup>
import { Route } from "lucide-vue-next";

import { useAppStore } from "../stores/app";

const app = useAppStore();
</script>

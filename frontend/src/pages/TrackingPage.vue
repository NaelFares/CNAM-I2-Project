<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mes courses</h1>
      <p class="page-subtitle">
        Chaque étape se confirme des deux côtés : vous et l'autre participant.
      </p>
    </header>

    <div v-if="!store.loaded && store.loading" class="text-sm text-slate-500">
      Chargement de vos courses…
    </div>

    <template v-else>
      <section class="space-y-4">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">En cours</h2>
        <div v-if="store.active.length" class="grid gap-4 lg:grid-cols-2">
          <TrackingCard v-for="tracking in store.active" :key="tracking.id" :tracking="tracking" />
        </div>
        <div v-else class="advice-banner">
          Aucune course en cours. Réservez un trajet depuis la page Covoiturage pour démarrer un suivi.
        </div>
      </section>

      <section v-if="store.finished.length" class="space-y-4">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">Historique</h2>
        <div class="grid gap-4 lg:grid-cols-2">
          <TrackingCard v-for="tracking in store.finished" :key="tracking.id" :tracking="tracking" />
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { onMounted } from "vue";

import TrackingCard from "../components/TrackingCard.vue";
import { useTrackingStore } from "../stores/tracking";

const store = useTrackingStore();

onMounted(() => store.load());
</script>

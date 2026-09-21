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

      <CarpoolSearchForm v-if="!quickSearchPerformed" @search="runQuickSearch" />

      <template v-else>
        <div class="flex justify-end">
          <Button variant="secondary" @click="resetQuickSearch">Nouvelle recherche</Button>
        </div>

        <RankedMatchesExplorer
          v-if="app.searchResults.length"
          :matches="app.searchResults"
          :reference-geometry="app.searchRouteGeometry"
        />

        <Card v-else>
          <p class="text-sm font-semibold text-slate-700">Aucun covoiturage compatible n’a été trouvé pour ce trajet.</p>
        </Card>
      </template>
    </div>

    <div v-show="activeTab === 'planning'" class="space-y-4">
      <div class="advice-banner">
        Conseil: plus le profil et le planning sont précis, plus le score de compatibilité est fiable.
      </div>

      <Card v-if="!planningSearchPerformed">
        <Button :disabled="app.loading" @click="runFullPlanningSearch">
          <UsersRound class="h-4 w-4" />
          Trouver un covoiturage
        </Button>
      </Card>

      <template v-else>
        <div class="flex justify-end">
          <Button variant="secondary" @click="resetPlanningSearch">Nouvelle recherche</Button>
        </div>

        <RankedMatchesExplorer v-if="app.matches.length" :matches="app.matches" />

        <Card v-else>
          <p class="text-sm font-semibold text-slate-700">Aucun covoiturage compatible n’a été trouvé dans votre planning.</p>
        </Card>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { UsersRound } from "lucide-vue-next";

import CarpoolSearchForm from "../components/CarpoolSearchForm.vue";
import RankedMatchesExplorer from "../components/RankedMatchesExplorer.vue";
import { Button, Card } from "../components/ui";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const activeTab = ref("quick");
const quickSearchPerformed = ref(false);
const planningSearchPerformed = ref(false);

async function runQuickSearch(payload) {
  const ok = await app.searchCarpoolTrip(payload);
  if (ok) quickSearchPerformed.value = true;
}

function resetQuickSearch() {
  quickSearchPerformed.value = false;
  app.searchResults = [];
  app.searchRouteGeometry = [];
}

async function runFullPlanningSearch() {
  const ok = await app.generateRides();
  if (!ok) return;

  const matchesFound = await app.findMatches();
  if (matchesFound) planningSearchPerformed.value = true;
}

function resetPlanningSearch() {
  planningSearchPerformed.value = false;
  app.matches = [];
}
</script>

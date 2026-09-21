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

      <RankedMatchesExplorer
        v-if="app.searchResults.length"
        :matches="app.searchResults"
        :reference-geometry="app.searchRouteGeometry"
      />
    </div>

    <div v-show="activeTab === 'planning'" class="space-y-4">
      <div class="advice-banner">
        Conseil: plus le profil et le planning sont précis, plus le score de compatibilité est fiable.
      </div>

      <Card>
        <Button :disabled="app.loading" @click="runFullPlanningSearch">
          <UsersRound class="h-4 w-4" />
          Trouver un covoiturage
        </Button>
      </Card>

      <RankedMatchesExplorer v-if="app.matches.length" :matches="app.matches" />
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

async function runFullPlanningSearch() {
  const ok = await app.generateRides();
  if (ok) await app.findMatches();
}
</script>

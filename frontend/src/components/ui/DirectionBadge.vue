<template>
  <span
    class="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold"
    :class="outbound ? 'bg-outbound-soft text-outbound' : 'bg-return-soft text-return'"
    :title="outbound ? 'Aller : vers le campus' : 'Retour : vers la maison'"
  >
    <component :is="outbound ? School : House" class="h-3.5 w-3.5" aria-hidden="true" />
    {{ outbound ? "Aller" : "Retour" }}
    <span v-if="time" class="font-medium opacity-80">· {{ outbound ? "arrivée" : "départ" }} {{ time }}</span>
  </span>
</template>

<script setup>
// Sens du trajet, identique sur toutes les pages :
// aller = vers le campus (heure d'arrivee), retour = vers la maison (heure de depart).
import { computed } from "vue";
import { House, School } from "lucide-vue-next";

import { isOutbound } from "../../lib/direction";

const props = defineProps({
  rideType: { type: String, default: "" },
  time: { type: String, default: "" },
});

const outbound = computed(() => isOutbound(props.rideType));
</script>

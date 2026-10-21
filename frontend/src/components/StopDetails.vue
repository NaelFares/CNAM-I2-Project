<template>
  <!-- Ce que le conducteur doit savoir avant d'accepter : ou et quand il
       passe, et ce que ca lui coute. Rien pour les demandes plus anciennes. -->
  <ul v-if="details.length" class="flex flex-wrap gap-x-3 gap-y-1 text-[0.8125rem] text-slate-600">
    <li v-for="detail in details" :key="detail.text" class="inline-flex items-center gap-1">
      <component :is="detail.icon" class="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
      {{ detail.text }}
    </li>
  </ul>
</template>

<script setup>
import { computed } from "vue";
import { Clock3, LogIn, LogOut, Route } from "lucide-vue-next";

import { isOutbound } from "../lib/direction";
import { formatMinutes } from "../lib/format";

const props = defineProps({
  ride: { type: Object, required: true },
  passenger: { type: Object, required: true },
});

const details = computed(() => {
  const list = [];
  const { passenger } = props;
  if (passenger.passage_time) {
    list.push({ icon: Clock3, text: `${isOutbound(props.ride.ride_type) ? "Dépose" : "Prise en charge"} ${passenger.passage_time}` });
  }
  if (passenger.pickup_on_the_way) list.push({ icon: LogIn, text: "Monte en chemin" });
  if (passenger.dropoff_on_the_way) list.push({ icon: LogOut, text: "Descend en chemin" });
  if (passenger.detour_min != null) list.push({ icon: Route, text: `+${formatMinutes(passenger.detour_min)}` });
  return list;
});
</script>

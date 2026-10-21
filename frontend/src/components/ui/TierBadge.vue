<template>
  <Badge :variant="variant" :title="title">
    <component :is="icon" class="h-3.5 w-3.5" />
    {{ tier.tier_label }}
  </Badge>
</template>

<script setup>
import { computed } from "vue";
import { Award, Medal, Sprout } from "lucide-vue-next";

import Badge from "./Badge.vue";

const props = defineProps({
  // ExperienceTierDTO : { rides_count, tier_key, tier_label, rides_to_next }
  tier: { type: Object, required: true },
});

const variant = computed(
  () => ({ expert: "success", intermediate: "primary" }[props.tier.tier_key] || "info")
);

const icon = computed(
  () => ({ expert: Award, intermediate: Medal }[props.tier.tier_key] || Sprout)
);

const title = computed(() => {
  const count = props.tier.rides_count;
  // Palier unique : les courses comptent quel que soit le role tenu.
  const base = `${count} course${count > 1 ? "s" : ""} terminée${count > 1 ? "s" : ""}`;
  // Au dernier palier il n'y a plus rien a atteindre : on n'affiche rien.
  return props.tier.rides_to_next
    ? `${base} — encore ${props.tier.rides_to_next} avant le palier suivant`
    : base;
});
</script>

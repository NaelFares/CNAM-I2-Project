<template>
  <div>
    <div :class="listClass">
      <template v-for="(item, index) in visibleItems" :key="itemKey ? item[itemKey] : index">
        <slot :item="item" :index="index" />
      </template>
    </div>
    <div v-if="items.length > limit" class="mt-3 flex justify-center">
      <button type="button" class="btn-ghost" @click="expanded = !expanded">
        <ChevronUp v-if="expanded" class="h-4 w-4" aria-hidden="true" />
        <ChevronDown v-else class="h-4 w-4" aria-hidden="true" />
        {{ expanded ? "Voir moins" : `Voir plus (${items.length - limit})` }}
      </button>
    </div>
  </div>
</template>

<script setup>
// Liste tronquee : affiche les premiers elements, le reste a la demande.
// Evite les pages qui s'allongent sans fin et les zones de defilement imbriquees.
import { computed, ref } from "vue";
import { ChevronDown, ChevronUp } from "lucide-vue-next";

const props = defineProps({
  items: { type: Array, required: true },
  limit: { type: Number, default: 5 },
  itemKey: { type: String, default: "" },
  listClass: { type: String, default: "space-y-3" },
});

const expanded = ref(false);
const visibleItems = computed(() => (expanded.value ? props.items : props.items.slice(0, props.limit)));
</script>

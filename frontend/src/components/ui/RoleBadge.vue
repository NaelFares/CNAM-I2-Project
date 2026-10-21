<template>
  <span
    class="inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold"
    :class="driver ? 'border-slate-800 bg-slate-800 text-white' : 'border-slate-300 bg-white text-slate-700'"
    :title="driver ? 'Vous conduisez' : 'Vous êtes passager'"
  >
    <component :is="driver ? CarFront : UserRound" class="h-3.5 w-3.5" aria-hidden="true" />
    {{ driver ? "Conducteur" : "Passager" }}
  </span>
</template>

<script setup>
// Role de l'utilisateur sur une course, identique sur toutes les pages :
// conducteur = pastille pleine (voiture), passager = pastille claire (personne).
import { computed } from "vue";
import { CarFront, UserRound } from "lucide-vue-next";

const props = defineProps({
  role: { type: String, required: true }, // 'driver' | 'passenger'
});

const driver = computed(() => props.role === "driver");
</script>

<template>
  <!-- Lecture seule : une simple representation visuelle -->
  <span v-if="readonly" class="inline-flex items-center gap-0.5" :title="title">
    <Star
      v-for="index in 5"
      :key="index"
      :class="['shrink-0', sizeClass, index <= Math.round(value) ? 'fill-amber-400 text-amber-400' : 'text-slate-300']"
    />
    <span v-if="showValue && value" class="ml-1 text-sm font-semibold text-slate-700">
      {{ value.toFixed(1) }}
    </span>
  </span>

  <!-- Saisie : chaque etoile est un bouton, navigable au clavier -->
  <span v-else class="inline-flex items-center gap-1" role="radiogroup" :aria-label="title">
    <button
      v-for="index in 5"
      :key="index"
      type="button"
      role="radio"
      :aria-checked="index === modelValue"
      :aria-label="`${index} étoile${index > 1 ? 's' : ''}`"
      class="rounded transition hover:scale-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      @click="$emit('update:modelValue', index)"
      @mouseenter="hovered = index"
      @mouseleave="hovered = 0"
    >
      <Star
        :class="['h-7 w-7', index <= (hovered || modelValue) ? 'fill-amber-400 text-amber-400' : 'text-slate-300']"
      />
    </button>
  </span>
</template>

<script setup>
import { computed, ref } from "vue";
import { Star } from "lucide-vue-next";

const props = defineProps({
  // Saisie : note choisie (0 = aucune).
  modelValue: { type: Number, default: 0 },
  // Lecture seule : moyenne a afficher.
  value: { type: Number, default: 0 },
  readonly: { type: Boolean, default: false },
  showValue: { type: Boolean, default: false },
  size: { type: String, default: "md" }, // 'sm' | 'md'
});

defineEmits(["update:modelValue"]);

const hovered = ref(0);

const sizeClass = computed(() => (props.size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4"));

const title = computed(() =>
  props.readonly
    ? props.value
      ? `${props.value.toFixed(1)} sur 5`
      : "Pas encore de note"
    : "Donner une note de 1 à 5 étoiles"
);
</script>

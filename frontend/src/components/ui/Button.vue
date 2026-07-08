<template>
  <button :type="type" :class="classes" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "primary" }, // 'primary' | 'secondary'
  type: { type: String, default: "button" },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
});

const classes = computed(() => [
  props.variant === "secondary" ? "btn-secondary" : "btn-primary",
  props.block ? "w-full" : "",
]);
</script>

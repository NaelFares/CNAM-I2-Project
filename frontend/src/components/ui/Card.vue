<template>
  <div :class="['card', paddingClass]">
    <slot />
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  padding: { type: String, default: "p-6" }, // 'p-6' | 'responsive' | 'none'
});

const paddingClass = computed(() => {
  if (props.padding === "responsive") return "p-6 md:p-7";
  if (props.padding === "none") return "";
  return props.padding;
});
</script>

<template>
  <span :class="['inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold', bgTextClasses]">
    <span v-if="dot" :class="['h-2 w-2 rounded-full', dotClasses]"></span>
    <slot />
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "primary" }, // 'primary' | 'success' | 'danger' | 'info'
  dot: { type: Boolean, default: false },
});

const bgTextClasses = computed(() => {
  const map = {
    primary: "bg-primary-soft text-primary",
    success: "bg-success-soft text-success",
    danger: "bg-danger-soft text-danger",
    info: "bg-info-soft text-info",
  };
  return map[props.variant] || map.primary;
});

const dotClasses = computed(() => {
  const map = {
    primary: "bg-primary",
    success: "bg-success",
    danger: "bg-danger",
    info: "bg-info",
  };
  return map[props.variant] || map.primary;
});
</script>

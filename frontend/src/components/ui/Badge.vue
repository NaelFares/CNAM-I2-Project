<template>
  <span :class="['inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold', bgTextClasses]">
    <span v-if="dot" :class="['h-2 w-2 rounded-full', dotClasses]"></span>
    <slot />
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "primary" }, // 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  dot: { type: Boolean, default: false },
});

const bgTextClasses = computed(() => {
  const map = {
    primary: "bg-primary-soft text-primary",
    success: "bg-success-soft text-success",
    warning: "bg-warning-soft text-warning",
    neutral: "bg-slate-100 text-slate-600",
    danger: "bg-danger-soft text-danger",
    info: "bg-info-soft text-info",
  };
  return map[props.variant] || map.primary;
});

const dotClasses = computed(() => {
  const map = {
    primary: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    neutral: "bg-slate-400",
    danger: "bg-danger",
    info: "bg-info",
  };
  return map[props.variant] || map.primary;
});
</script>

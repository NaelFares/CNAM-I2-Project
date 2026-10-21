<template>
  <div class="flex flex-col items-center gap-3 rounded-[var(--radius-card)] border border-dashed border-slate-300 bg-white px-6 py-8 text-center">
    <span v-if="icon" class="grid h-10 w-10 place-items-center rounded-full bg-slate-100 text-slate-500">
      <component :is="icon" class="h-5 w-5" aria-hidden="true" />
    </span>
    <div class="space-y-1">
      <p class="card-title">{{ title }}</p>
      <p v-if="text" class="muted mx-auto max-w-sm">{{ text }}</p>
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: [Object, Function], default: null },
  title: { type: String, required: true },
  text: { type: String, default: "" },
});
</script>

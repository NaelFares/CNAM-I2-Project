<template>
  <div class="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
    <div class="min-w-0">
      <h2 class="section-title flex items-center gap-2">
        <slot name="icon" />
        {{ title }}
        <span v-if="count !== null" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
          {{ count }}
        </span>
      </h2>
      <p v-if="subtitle" class="muted mt-0.5">{{ subtitle }}</p>
    </div>
    <slot name="action" />
  </div>
</template>

<script setup>
// Titre de section commun : toujours plus visible que le contenu qu'il annonce.
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  count: { type: Number, default: null },
});
</script>

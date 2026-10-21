<template>
  <transition name="toast">
    <div v-if="feedback.text" class="pointer-events-none fixed right-4 top-20 z-50 w-[min(92vw,24rem)]" role="status" aria-live="polite">
      <div class="pointer-events-auto rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.12)]">
        <div class="flex items-start gap-3">
          <component :is="currentIcon" class="mt-0.5 h-5 w-5 shrink-0" :class="toneClass" aria-hidden="true" />
          <p class="flex-1 text-sm font-medium leading-relaxed text-slate-800">{{ feedback.text }}</p>
          <button class="-mr-1 rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700" aria-label="Fermer" @click="feedback.clear">
            <X class="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, watch } from "vue";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-vue-next";

import { useFeedbackStore } from "../stores/feedback";

const feedback = useFeedbackStore();

const toneClass = computed(() => {
  if (feedback.kind === "error") {
    return "text-danger";
  }
  if (feedback.kind === "info") {
    return "text-info";
  }
  return "text-success";
});

const currentIcon = computed(() => {
  if (feedback.kind === "error") return AlertCircle;
  if (feedback.kind === "info") return Info;
  return CheckCircle2;
});

watch(
  () => feedback.token,
  () => {
    if (!feedback.text) return;
    setTimeout(() => feedback.clear(), 5000);
  }
);
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

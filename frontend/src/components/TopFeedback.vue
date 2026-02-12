<template>
  <transition name="toast">
    <div v-if="feedback.text" class="pointer-events-none fixed left-1/2 top-[5.75rem] z-30 w-[min(94vw,40rem)] -translate-x-1/2 md:top-[6.25rem]">
      <div class="pointer-events-auto rounded-2xl border px-4 py-3 shadow-[0_14px_32px_rgba(18,33,59,0.18)] backdrop-blur-sm" :class="toneClass">
        <div class="flex items-start gap-3">
          <component :is="currentIcon" class="mt-0.5 h-5 w-5 shrink-0" />
          <p class="flex-1 text-sm font-semibold leading-relaxed">{{ feedback.text }}</p>
          <button class="rounded-md px-2 py-1 text-xs font-bold opacity-80 transition hover:opacity-100" @click="feedback.clear">
            Fermer
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, watch } from "vue";
import { AlertCircle, CheckCircle2, Info } from "lucide-vue-next";

import { useFeedbackStore } from "../stores/feedback";

const feedback = useFeedbackStore();

const toneClass = computed(() => {
  if (feedback.kind === "error") {
    return "border-rose-200 bg-rose-50/95 text-rose-800";
  }
  if (feedback.kind === "info") {
    return "border-sky-200 bg-sky-50/95 text-sky-800";
  }
  return "border-emerald-200 bg-emerald-50/95 text-emerald-800";
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
  transform: translate(-50%, -10px);
}
</style>

<template>
  <Transition name="loading-fade">
    <div
      v-if="app.loading"
      class="loading-overlay"
      role="status"
      aria-live="polite"
      :aria-busy="app.loading ? 'true' : 'false'"
    >
      <div class="loading-panel">
        <LoadingAnimation class="mb-4" />

        <p class="loading-title">{{ app.loadingLabel || "Traitement en cours..." }}</p>
        <p v-if="app.loadingDetail" class="loading-detail">{{ app.loadingDetail }}</p>
        <p v-if="elapsedLabel" class="loading-time">{{ elapsedLabel }}</p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";

import LoadingAnimation from "./LoadingAnimation.vue";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const now = ref(Date.now());
let timerId = null;

const stopTimer = () => {
  if (timerId !== null) {
    clearInterval(timerId);
    timerId = null;
  }
};

const startTimer = () => {
  stopTimer();
  now.value = Date.now();
  timerId = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
};

watch(
  () => app.loading,
  (loading) => {
    if (loading) {
      startTimer();
    } else {
      stopTimer();
    }
  },
  { immediate: true }
);

onBeforeUnmount(stopTimer);

const elapsedLabel = computed(() => {
  if (!app.loadingStartedAt) {
    return "";
  }

  const elapsedSeconds = Math.max(0, Math.floor((now.value - app.loadingStartedAt) / 1000));
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  if (minutes > 0) {
    return `${minutes} min ${String(seconds).padStart(2, "0")} s`;
  }
  return `${seconds} s`;
});
</script>

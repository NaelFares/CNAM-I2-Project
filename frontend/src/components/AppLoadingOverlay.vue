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
        <div class="orbit-loader" aria-hidden="true">
          <div class="orbit-track"></div>
          <div class="orbit-lane"></div>
          <div class="orbit-core"></div>
          <div class="orbit-car">
            <svg class="orbit-car-svg" viewBox="0 0 72 44" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M14 28h44c3.2 0 5.8-2.6 5.8-5.8v-.2c0-2.8-1.9-5.3-4.6-6l-7-1.8c-1.8-.5-3.4-1.5-4.5-3l-2.7-3.7C43.7 5.5 41.1 4 38.3 4H26.8c-3.7 0-7.1 1.9-9.2 5l-4.3 6.5-4.8.9A6.1 6.1 0 0 0 3.5 22v.2C3.5 25.4 6.1 28 9.3 28H14Z"
                fill="var(--color-primary)"
              />
              <path
                d="M22 12.5c.8-1.3 2.2-2.1 3.8-2.1h11.8c1.6 0 3.1.8 3.9 2.1l2.7 4.2H19.4l2.6-4.2Z"
                fill="var(--color-primary-soft)"
              />
              <circle cx="20" cy="30.5" r="6.2" fill="var(--color-primary-strong)" />
              <circle cx="52" cy="30.5" r="6.2" fill="var(--color-primary-strong)" />
              <circle cx="20" cy="30.5" r="2.7" fill="#dbe8ff" />
              <circle cx="52" cy="30.5" r="2.7" fill="#dbe8ff" />
              <rect x="27.5" y="18.4" width="17" height="3.8" rx="1.9" fill="var(--color-primary-soft)" />
            </svg>
          </div>
          <div class="orbit-dots">
            <span class="orbit-dot"></span>
            <span class="orbit-dot"></span>
            <span class="orbit-dot"></span>
          </div>
        </div>

        <p class="loading-title">{{ app.loadingLabel || "Traitement en cours..." }}</p>
        <p v-if="app.loadingDetail" class="loading-detail">{{ app.loadingDetail }}</p>
        <p v-if="elapsedLabel" class="loading-time">{{ elapsedLabel }}</p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";

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
    return `Temps ecoule: ${minutes}m ${String(seconds).padStart(2, "0")}s`;
  }
  return `Temps ecoule: ${seconds}s`;
});
</script>

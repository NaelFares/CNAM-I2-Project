<template>
  <div class="app-shell">
    <AppBackground />
    <div class="content-layer">
      <TopFeedback />
      <AppLoadingOverlay />
      <RouterView />
    </div>
  </div>
</template>

<script setup>
import AppBackground from "./components/AppBackground.vue";
import AppLoadingOverlay from "./components/AppLoadingOverlay.vue";
import TopFeedback from "./components/TopFeedback.vue";
</script>


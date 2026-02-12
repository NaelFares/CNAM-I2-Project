<template>
  <div class="app-shell">
    <AppBackground />
    <div class="content-layer">
      <TopFeedback />
      <RouterView />
    </div>
  </div>
</template>

<script setup>
import AppBackground from "./components/AppBackground.vue";
import TopFeedback from "./components/TopFeedback.vue";
</script>


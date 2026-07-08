<template>
  <div class="background-root" aria-hidden="true">
    <span class="mesh"></span>
  </div>
</template>

<style scoped>
.background-root {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.mesh {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(15, 35, 58, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 35, 58, 0.07) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.34));
}
</style>

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
  /* Fond neutre uni : la grille decorative chargeait visuellement les pages. */
  position: absolute;
  inset: 0;
  background: var(--color-bg);
}
</style>

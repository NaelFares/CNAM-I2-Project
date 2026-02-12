<template>
  <div class="background-root" aria-hidden="true">
    <span class="orb orb-a"></span>
    <span class="orb orb-b"></span>
    <span class="orb orb-c"></span>
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

.orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(16px);
  opacity: 0.46;
  will-change: transform;
}

.orb-a {
  width: 40rem;
  height: 40rem;
  top: -18rem;
  left: -10rem;
  background: radial-gradient(circle, rgba(72, 146, 255, 0.5), rgba(72, 146, 255, 0));
  animation: drift-a 34s ease-in-out infinite;
}

.orb-b {
  width: 30rem;
  height: 30rem;
  top: 10%;
  right: -9rem;
  background: radial-gradient(circle, rgba(31, 168, 255, 0.34), rgba(31, 168, 255, 0));
  animation: drift-b 42s ease-in-out infinite;
}

.orb-c {
  width: 32rem;
  height: 32rem;
  bottom: -14rem;
  left: 35%;
  background: radial-gradient(circle, rgba(78, 118, 255, 0.3), rgba(78, 118, 255, 0));
  animation: drift-c 36s ease-in-out infinite;
}

.mesh {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(15, 35, 58, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 35, 58, 0.055) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.34));
}

@keyframes drift-a {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(30px, 22px, 0);
  }
}

@keyframes drift-b {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(-32px, 18px, 0);
  }
}

@keyframes drift-c {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(22px, -28px, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .orb-a,
  .orb-b,
  .orb-c {
    animation: none;
  }
}
</style>

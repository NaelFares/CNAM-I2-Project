<template>
  <svg class="ride-strip" viewBox="0 0 240 44" aria-hidden="true">
    <path class="ride-strip__road" d="M20 32 H220" />
    <path class="ride-strip__trail" d="M20 32 H220" pathLength="100" />
    <path class="ride-strip__line" d="M20 32 H220" />
    <circle class="ride-strip__origin" cx="20" cy="32" r="4.5" />

    <g transform="translate(220 30)">
      <path class="ride-strip__pin ride-strip__pin--campus" transform="scale(0.95)" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
      <path class="ride-strip__glyph" d="M-4.6 -13 L0 -20.4 L4.6 -13 Z M-3.8 -12.2 h7.6 v1.6 h-7.6 Z" />
    </g>

    <g transform="translate(120 27)">
      <g class="ride-strip__rider">
        <g transform="scale(0.85)">
          <path class="ride-strip__pin" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
          <circle class="ride-strip__disc" cy="-17" r="6.2" />
          <circle class="ride-strip__person" cy="-19.2" r="2.1" />
          <path class="ride-strip__person" d="M-3.7 -13.2 a3.7 3.4 0 0 1 7.4 0 Z" />
        </g>
      </g>
    </g>

    <g class="ride-strip__car">
      <rect class="ride-strip__car-body" x="-10" y="-5.5" width="20" height="11" rx="4.5" />
      <path class="ride-strip__car-glass" d="M2.4 -3.8 L5.4 -3.2 Q6.4 0 5.4 3.2 L2.4 3.8 Z" />
      <rect class="ride-strip__car-glass" x="-6.4" y="-3.4" width="2" height="6.8" rx="1" />
    </g>
  </svg>
</template>

<style scoped>
.ride-strip {
  --strip-orange: #fd8501;
  --strip-loop: 7s;
  display: block;
  width: 100%;
  height: auto;
}

.ride-strip__road,
.ride-strip__trail,
.ride-strip__line {
  fill: none;
  stroke-linecap: round;
}

.ride-strip__road {
  stroke: var(--color-stroke-strong);
  stroke-width: 7;
}

.ride-strip__trail {
  stroke: var(--color-primary);
  stroke-width: 7;
  stroke-dasharray: 100;
  stroke-dashoffset: 50;
  animation: strip-trail var(--strip-loop) infinite;
}

.ride-strip__line {
  stroke: var(--color-surface);
  stroke-width: 1;
  stroke-dasharray: 4 5;
  opacity: 0.9;
}

.ride-strip__origin {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 2.6;
}

.ride-strip__pin {
  fill: var(--strip-orange);
  stroke: var(--color-surface);
  stroke-width: 1.5;
  stroke-linejoin: round;
}

.ride-strip__pin--campus {
  fill: var(--color-primary);
}

.ride-strip__glyph,
.ride-strip__disc {
  fill: var(--color-surface);
}

.ride-strip__person {
  fill: var(--strip-orange);
}

.ride-strip__rider {
  animation: strip-rider var(--strip-loop) infinite;
}

.ride-strip__car {
  transform: translate(120px, 32px);
  animation: strip-car var(--strip-loop) infinite;
}

.ride-strip__car-body {
  fill: var(--color-surface);
  stroke: var(--color-text);
  stroke-width: 1.3;
}

.ride-strip__car-glass {
  fill: var(--color-text);
}

/* Boucle : départ, arrêt pour l'étudiant à mi-parcours, arrivée au campus. */
@keyframes strip-car {
  0% { transform: translate(20px, 32px); opacity: 0; }
  5% { transform: translate(20px, 32px); opacity: 1; animation-timing-function: ease-in-out; }
  32%, 44% { transform: translate(120px, 32px); animation-timing-function: ease-in-out; }
  72% { transform: translate(208px, 32px); }
  92% { transform: translate(208px, 32px); opacity: 1; }
  100% { transform: translate(208px, 32px); opacity: 0; }
}

@keyframes strip-trail {
  0%, 5% { stroke-dashoffset: 100; opacity: 1; animation-timing-function: ease-in-out; }
  32%, 44% { stroke-dashoffset: 50; animation-timing-function: ease-in-out; }
  72% { stroke-dashoffset: 6; }
  92% { stroke-dashoffset: 6; opacity: 1; }
  100% { stroke-dashoffset: 6; opacity: 0; }
}

@keyframes strip-rider {
  0%, 34% { transform: translateY(0) scale(1); opacity: 1; animation-timing-function: ease-out; }
  38% { transform: translateY(-4px) scale(1); opacity: 1; animation-timing-function: ease-in; }
  42%, 94% { transform: translateY(5px) scale(0); opacity: 0; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .ride-strip * {
    animation: none !important;
  }
}
</style>

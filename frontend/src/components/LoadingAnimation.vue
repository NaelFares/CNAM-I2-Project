<template>
  <!-- Meme direction artistique que StepAnimation (tableau de bord), en plus
       compact : la voiture fait la navette maison -> campus en boucle. -->
  <svg class="load-anim" viewBox="0 0 200 84" aria-hidden="true">
    <rect class="load-anim__bg" width="200" height="84" rx="16" />

    <g class="load-anim__lots">
      <rect x="10" y="8" width="38" height="24" rx="6" />
      <rect x="84" y="50" width="34" height="26" rx="6" />
      <rect x="132" y="8" width="30" height="20" rx="6" />
    </g>
    <circle class="load-anim__tree" cx="66" cy="18" r="5" />
    <circle class="load-anim__tree" cx="148" cy="66" r="5" />
    <circle class="load-anim__tree" cx="20" cy="70" r="4" />

    <path class="load-anim__road" :d="ROUTE" />
    <path class="load-anim__route" :d="ROUTE" pathLength="100" />

    <!-- Depart : la maison -->
    <g transform="translate(26 54)">
      <rect class="load-anim__house" x="-8" y="-6" width="16" height="13" rx="3" />
      <path class="load-anim__roof" d="M-10 -5 L0 -13 L10 -5 Z" />
    </g>

    <!-- Arrivee : le campus -->
    <g transform="translate(176 40)">
      <circle class="load-anim__arrive" cy="-12" r="14" />
      <path class="load-anim__pin" transform="scale(1.05)" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
      <path class="load-anim__glyph" d="M-5 -15.5 L0 -23 L5 -15.5 Z M-4.2 -14.6 h8.4 v1.8 h-8.4 Z" />
    </g>

    <g class="load-anim__car">
      <rect class="load-anim__car-shadow" x="-9.5" y="-4.5" width="20" height="11" rx="4.5" />
      <rect class="load-anim__car-body" x="-10" y="-5.5" width="20" height="11" rx="4.5" />
      <path class="load-anim__car-glass" d="M2.4 -3.8 L5.4 -3.2 Q6.4 0 5.4 3.2 L2.4 3.8 Z" />
      <rect class="load-anim__car-glass" x="-6.4" y="-3.4" width="2" height="6.8" rx="1" />
    </g>
  </svg>
</template>

<script setup>
// Meme trace que offset-path dans le CSS ci-dessous.
const ROUTE = "M26 54 C50 54 56 36 82 36 C110 36 118 50 142 46 C158 43 166 34 176 30";
</script>

<style scoped>
.load-anim {
  --loop: 2.6s;
  display: block;
  width: 100%;
  max-width: 220px;
  height: auto;
  margin: 0 auto;
}

.load-anim__bg { fill: var(--color-primary-soft); }
.load-anim__lots rect { fill: #dbe7fb; }
.load-anim__tree { fill: #9fd6b7; }

.load-anim__road {
  fill: none;
  stroke: var(--color-surface);
  stroke-width: 10;
  stroke-linecap: round;
}

.load-anim__route {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-dasharray: 100;
  animation: load-route var(--loop) ease-in-out infinite;
}

.load-anim__house { fill: var(--color-surface); stroke: var(--color-stroke-strong); stroke-width: 1.2; }
.load-anim__roof { fill: #fd8501; }
.load-anim__pin { fill: var(--color-primary); stroke: var(--color-surface); stroke-width: 1.5; stroke-linejoin: round; }
.load-anim__glyph { fill: var(--color-surface); }

.load-anim__arrive {
  fill: var(--color-primary);
  opacity: 0;
  transform-box: fill-box;
  transform-origin: center;
  animation: load-arrive var(--loop) ease-out infinite;
}

.load-anim__car {
  offset-path: path("M26 54 C50 54 56 36 82 36 C110 36 118 50 142 46 C158 43 166 34 176 30");
  offset-rotate: auto;
  animation: load-car var(--loop) ease-in-out infinite;
}

.load-anim__car-shadow { fill: var(--color-text); opacity: 0.2; }
.load-anim__car-body { fill: var(--color-surface); stroke: var(--color-text); stroke-width: 1.3; }
.load-anim__car-glass { fill: var(--color-text); }

@keyframes load-car {
  0% { offset-distance: 0%; opacity: 0; }
  8% { opacity: 1; }
  82% { offset-distance: 100%; opacity: 1; }
  92%, 100% { offset-distance: 100%; opacity: 0; }
}

@keyframes load-route {
  0% { stroke-dashoffset: 100; }
  82% { stroke-dashoffset: 0; opacity: 1; }
  100% { stroke-dashoffset: 0; opacity: 0; }
}

@keyframes load-arrive {
  0%, 78% { opacity: 0; transform: scale(0.4); }
  84% { opacity: 0.25; }
  100% { opacity: 0; transform: scale(1.3); }
}

@media (prefers-reduced-motion: reduce) {
  .load-anim__car { animation: none; offset-distance: 55%; }
  .load-anim__route { animation: none; stroke-dashoffset: 0; }
}
</style>

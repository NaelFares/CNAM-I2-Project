<template>
  <svg class="step-anim" :class="`step-anim--${variant}`" viewBox="0 0 240 130" aria-hidden="true">
    <rect class="step-anim__bg" width="240" height="130" rx="18" />

    <!-- Import du planning : les cours du fichier remplissent la semaine -->
    <template v-if="variant === 'import'">
      <circle class="step-anim__glow" cx="52" cy="66" r="44" />

      <path class="step-anim__link" d="M82 62 C94 48 106 48 118 60" />
      <circle v-for="n in 3" :key="`d-${n}`" class="step-anim__data" :class="`step-anim__data--${n}`" r="3.2" />

      <g transform="translate(52 66)">
        <g class="step-anim__file">
          <path class="step-anim__shadow" d="M-19 -26 h28 l16 16 v44 a4 4 0 0 1 -4 4 h-36 a4 4 0 0 1 -4 -4 Z" />
          <path class="step-anim__paper" d="M-22 -26 a4 4 0 0 1 4 -4 h24 l16 16 v44 a4 4 0 0 1 -4 4 h-36 a4 4 0 0 1 -4 -4 Z" />
          <path class="step-anim__fold" d="M6 -30 v12 a4 4 0 0 0 4 4 h12 Z" />
          <g class="step-anim__paper-lines">
            <path d="M-14 -8 H8" />
            <path d="M-14 0 H14" />
            <path d="M-14 8 H2" />
          </g>
          <rect class="step-anim__tag" x="-16" y="16" width="32" height="13" rx="4.5" />
          <circle v-for="n in 3" :key="`tag-${n}`" class="step-anim__tag-dot" :cx="(n - 2) * 7" cy="22.5" r="1.8" />
        </g>
      </g>

      <rect class="step-anim__shadow" x="123" y="20" width="104" height="98" rx="12" />
      <rect class="step-anim__paper" x="120" y="16" width="104" height="98" rx="12" />
      <path class="step-anim__cal-head" d="M120 38 V28 a12 12 0 0 1 12 -12 h80 a12 12 0 0 1 12 12 V38 Z" />
      <g class="step-anim__cal-rings">
        <path d="M144 11 V21" />
        <path d="M200 11 V21" />
      </g>
      <circle v-for="col in 5" :key="`day-${col}`" class="step-anim__cal-day" :cx="CAL_X + (col - 1) * CAL_STEP + 7.5" cy="30" r="1.8" />
      <rect v-for="col in 5" :key="`col-${col}`" class="step-anim__cal-col" :x="CAL_X + (col - 1) * CAL_STEP" y="44" width="15" height="64" rx="4" />
      <rect
        v-for="(event, i) in EVENTS"
        :key="`e-${i}`"
        class="step-anim__event"
        :class="`step-anim__event--${i + 1}`"
        :x="CAL_X + event[0] * CAL_STEP"
        :y="event[1]"
        width="15"
        :height="event[2]"
        rx="4"
        :style="{ fill: event[3] }"
      />
      <g transform="translate(222 18)">
        <g class="step-anim__check">
          <circle r="11" />
          <path d="M-4.6 0.4 L-1.4 3.6 L5 -3.2" />
        </g>
      </g>
    </template>

    <!-- Profil : adresse saisie, pin posé sur la carte, rôle et tolérance réglés -->
    <template v-else-if="variant === 'profile'">
      <defs>
        <clipPath id="step-anim-map-clip">
          <rect x="122" y="14" width="104" height="102" rx="12" />
        </clipPath>
      </defs>

      <rect class="step-anim__shadow" x="17" y="18" width="96" height="102" rx="12" />
      <rect class="step-anim__paper" x="14" y="14" width="96" height="102" rx="12" />
      <circle class="step-anim__avatar" cx="36" cy="36" r="12" />
      <circle class="step-anim__avatar-person" cx="36" cy="32.8" r="3.6" />
      <path class="step-anim__avatar-person" d="M29.6 43 a6.4 5.6 0 0 1 12.8 0 Z" />
      <rect class="step-anim__bar step-anim__bar--strong" x="56" y="29" width="40" height="6" rx="3" />
      <rect class="step-anim__bar" x="56" y="40" width="26" height="5" rx="2.5" />

      <rect class="step-anim__field" x="24" y="56" width="76" height="15" rx="5" />
      <path class="step-anim__field-pin" d="M32.5 68 L29.5 63.8 A3.7 3.7 0 1 1 35.5 63.8 Z" />
      <rect class="step-anim__typed" x="41" y="61" width="50" height="5" rx="2.5" />

      <rect class="step-anim__field" x="24" y="77" width="76" height="13" rx="6.5" />
      <rect class="step-anim__knob" x="24" y="77" width="38" height="13" rx="6.5" />
      <rect class="step-anim__toggle-label step-anim__toggle-label--left" x="35" y="82" width="16" height="3" rx="1.5" />
      <rect class="step-anim__toggle-label step-anim__toggle-label--right" x="73" y="82" width="16" height="3" rx="1.5" />

      <path class="step-anim__track" d="M27 103 H97" />
      <path class="step-anim__track-fill" d="M27 103 H97" pathLength="100" />
      <circle class="step-anim__thumb" cx="27" cy="103" r="5" />

      <g clip-path="url(#step-anim-map-clip)">
        <rect class="step-anim__map" x="122" y="14" width="104" height="102" />
        <g class="step-anim__lots">
          <rect x="126" y="18" width="34" height="50" rx="6" />
          <rect x="176" y="18" width="30" height="50" rx="6" />
          <rect x="126" y="88" width="34" height="26" rx="6" />
        </g>
        <rect class="step-anim__green" x="176" y="88" width="48" height="26" rx="6" />
        <circle class="step-anim__tree" cx="190" cy="100" r="6" />
        <circle class="step-anim__tree" cx="208" cy="104" r="5" />
        <g class="step-anim__streets">
          <path d="M122 78 H226" />
          <path d="M168 14 V116" />
          <path d="M230 14 L206 78" />
        </g>
        <rect class="step-anim__shadow" x="181" y="47" width="22" height="22" rx="4" />
        <rect class="step-anim__house" x="179" y="44" width="22" height="22" rx="4" />
        <path class="step-anim__house-ridge" d="M184 55 H196" />
      </g>
      <rect class="step-anim__map-frame" x="122" y="14" width="104" height="102" rx="12" />

      <g transform="translate(190 60)">
        <ellipse class="step-anim__ripple" rx="20" ry="8" />
        <ellipse class="step-anim__pin-shadow" rx="7" ry="2.6" />
        <g class="step-anim__drop">
          <g transform="scale(1.2)">
            <path class="step-anim__pin-body" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
            <circle class="step-anim__pin-disc" cy="-17" r="4.6" />
          </g>
        </g>
      </g>
    </template>

    <!-- Covoiturage : le trajet se trace, les étudiants montent à bord, arrivée au campus -->
    <template v-else>
      <g class="step-anim__lots">
        <rect x="14" y="14" width="52" height="36" rx="8" />
        <rect x="122" y="14" width="56" height="26" rx="8" />
        <rect x="78" y="84" width="40" height="32" rx="8" />
      </g>
      <circle class="step-anim__tree" cx="132" cy="110" r="6" />
      <circle class="step-anim__tree" cx="26" cy="68" r="6" />
      <circle class="step-anim__tree" cx="222" cy="78" r="5" />

      <path class="step-anim__route-base" :d="ROUTE" />
      <path class="step-anim__route" :d="ROUTE" pathLength="100" />
      <circle class="step-anim__origin" cx="30" cy="98" r="4.5" />

      <g transform="translate(204 44)">
        <path class="step-anim__pin-body step-anim__pin-body--campus" transform="scale(1.3)" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
        <path class="step-anim__campus-glyph" d="M-6 -17.5 L0 -27 L6 -17.5 Z M-5 -16.5 h10 v2 h-10 Z" />
        <circle class="step-anim__arrive" cy="-20" r="20" />
      </g>

      <g v-for="rider in RIDERS" :key="rider.id" :transform="`translate(${rider.x} ${rider.y})`">
        <g class="step-anim__rider" :class="`step-anim__rider--${rider.id}`">
          <g transform="scale(1.15)">
            <path class="step-anim__pin-body" d="M0 0 L-8.1 -11.2 A10 10 0 1 1 8.1 -11.2 Z" />
            <circle class="step-anim__pin-disc" cy="-17" r="6.2" />
            <circle class="step-anim__pin-person" cy="-19.2" r="2.1" />
            <path class="step-anim__pin-person" d="M-3.7 -13.2 a3.7 3.4 0 0 1 7.4 0 Z" />
          </g>
        </g>
      </g>

      <g class="step-anim__car">
        <rect class="step-anim__car-shadow" x="-9.5" y="-4.5" width="20" height="11" rx="4.5" />
        <rect class="step-anim__car-body" x="-10" y="-5.5" width="20" height="11" rx="4.5" />
        <path class="step-anim__car-glass" d="M2.4 -3.8 L5.4 -3.2 Q6.4 0 5.4 3.2 L2.4 3.8 Z" />
        <rect class="step-anim__car-glass" x="-6.4" y="-3.4" width="2" height="6.8" rx="1" />
      </g>

      <g transform="translate(148 99)">
        <rect class="step-anim__shadow" x="2" y="3" width="80" height="24" rx="12" />
        <rect class="step-anim__paper" width="80" height="24" rx="12" />
        <g transform="translate(15 12)">
          <circle class="step-anim__seat step-anim__seat--driver" r="7.5" />
          <circle class="step-anim__seat-person" cy="-2" r="2.3" />
          <path class="step-anim__seat-person" d="M-4 4.4 a4 3.6 0 0 1 8 0 Z" />
        </g>
        <g v-for="n in 2" :key="`s-${n}`" :transform="`translate(${15 + n * 17} 12)`">
          <circle class="step-anim__seat step-anim__seat--empty" r="6.8" />
          <g class="step-anim__boarded" :class="`step-anim__boarded--${n}`">
            <circle class="step-anim__seat step-anim__seat--rider" r="7.5" />
            <circle class="step-anim__seat-person" cy="-2" r="2.3" />
            <path class="step-anim__seat-person" d="M-4 4.4 a4 3.6 0 0 1 8 0 Z" />
          </g>
        </g>
        <g transform="translate(67 12)">
          <circle class="step-anim__seat step-anim__seat--empty" r="6.8" />
          <g class="step-anim__check step-anim__check--trip">
            <circle r="7.5" />
            <path d="M-3.2 0.3 L-1 2.5 L3.4 -2.2" />
          </g>
        </g>
      </g>
    </template>
  </svg>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    required: true,
    validator: (value) => ["import", "profile", "carpool"].includes(value),
  },
});

// Calendrier : abscisse de la première colonne et pas entre colonnes.
const CAL_X = 128;
const CAL_STEP = 18.4;

// [colonne, y, hauteur, couleur]
const EVENTS = [
  [0, 46, 22, "#1d4ed8"],
  [1, 58, 30, "#fd8501"],
  [2, 46, 16, "#6f9bf5"],
  [3, 72, 32, "#1d4ed8"],
  [4, 52, 20, "#2fae77"],
  [2, 70, 26, "#fd8501"],
];

// Même tracé que offset-path dans le CSS ci-dessous ; les étudiants sont aux jonctions (37 % et 74,5 %).
const ROUTE = "M30 98 C60 98 62 60 96 58 C132 56 136 92 170 84 C192 79 200 58 204 44";
const RIDERS = [
  { id: 1, x: 96, y: 58 },
  { id: 2, x: 170, y: 84 },
];
</script>

<style scoped>
.step-anim {
  --step-orange: #fd8501;
  --step-loop: 6s;
  display: block;
  width: 100%;
  height: auto;
}

.step-anim__bg {
  fill: var(--color-primary-soft);
}

.step-anim__glow {
  fill: var(--color-surface);
  opacity: 0.55;
}

.step-anim__shadow {
  fill: var(--color-text);
  opacity: 0.08;
}

.step-anim__paper {
  fill: var(--color-surface);
  stroke: var(--color-stroke-strong);
  stroke-width: 1.4;
  stroke-linejoin: round;
}

.step-anim__check {
  transform: scale(0);
  animation: step-check var(--step-loop) infinite;
}

.step-anim__check circle {
  fill: var(--color-success);
  stroke: var(--color-surface);
  stroke-width: 2;
}

.step-anim__check path {
  fill: none;
  stroke: var(--color-surface);
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.step-anim__check--trip circle {
  stroke: none;
}

.step-anim__check--trip path {
  stroke-width: 1.8;
}

/* --- Import --- */
.step-anim__file {
  animation: step-float 3s ease-in-out infinite alternate;
}

.step-anim__fold {
  fill: var(--color-primary-soft);
  stroke: var(--color-stroke-strong);
  stroke-width: 1.4;
  stroke-linejoin: round;
}

.step-anim__paper-lines path {
  stroke: var(--color-stroke-strong);
  stroke-width: 3;
  stroke-linecap: round;
}

.step-anim__tag {
  fill: var(--color-primary);
}

.step-anim__tag-dot {
  fill: var(--color-surface);
}

.step-anim__link {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-dasharray: 2 4;
  opacity: 0.45;
}

.step-anim__data {
  fill: var(--color-primary);
  opacity: 0;
  offset-path: path("M82 62 C94 48 106 48 118 60");
  animation: step-data var(--step-loop) infinite;
}

.step-anim__data--2 { animation-name: step-data-2; }
.step-anim__data--3 { animation-name: step-data-3; }

.step-anim__cal-head {
  fill: var(--color-primary);
}

.step-anim__cal-rings path {
  stroke: var(--color-primary-strong);
  stroke-width: 3.4;
  stroke-linecap: round;
}

.step-anim__cal-day {
  fill: var(--color-surface);
  opacity: 0.85;
}

.step-anim__cal-col {
  fill: var(--color-surface-soft);
  stroke: var(--color-stroke);
  stroke-width: 0.8;
}

.step-anim__event {
  transform-box: fill-box;
  transform-origin: center top;
  animation: step-event-1 var(--step-loop) infinite;
}

.step-anim__event--2 { animation-name: step-event-2; }
.step-anim__event--3 { animation-name: step-event-3; }
.step-anim__event--4 { animation-name: step-event-4; }
.step-anim__event--5 { animation-name: step-event-5; }
.step-anim__event--6 { animation-name: step-event-6; }

@keyframes step-float {
  from { transform: translateY(-2px) rotate(-3deg); }
  to { transform: translateY(2px) rotate(-1deg); }
}

@keyframes step-data {
  0%, 8% { offset-distance: 0%; opacity: 0; }
  10% { offset-distance: 0%; opacity: 1; }
  24% { offset-distance: 100%; opacity: 1; }
  26%, 100% { offset-distance: 100%; opacity: 0; }
}

@keyframes step-data-2 {
  0%, 18% { offset-distance: 0%; opacity: 0; }
  20% { offset-distance: 0%; opacity: 1; }
  34% { offset-distance: 100%; opacity: 1; }
  36%, 100% { offset-distance: 100%; opacity: 0; }
}

@keyframes step-data-3 {
  0%, 28% { offset-distance: 0%; opacity: 0; }
  30% { offset-distance: 0%; opacity: 1; }
  44% { offset-distance: 100%; opacity: 1; }
  46%, 100% { offset-distance: 100%; opacity: 0; }
}

@keyframes step-event-1 {
  0%, 24% { transform: scaleY(0); opacity: 1; }
  30%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-event-2 {
  0%, 30% { transform: scaleY(0); opacity: 1; }
  36%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-event-3 {
  0%, 36% { transform: scaleY(0); opacity: 1; }
  42%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-event-4 {
  0%, 42% { transform: scaleY(0); opacity: 1; }
  48%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-event-5 {
  0%, 48% { transform: scaleY(0); opacity: 1; }
  54%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-event-6 {
  0%, 54% { transform: scaleY(0); opacity: 1; }
  60%, 92% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(1); opacity: 0; }
}

@keyframes step-check {
  0%, 64% { transform: scale(0); opacity: 1; }
  69% { transform: scale(1.2); }
  73%, 92% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

/* --- Profil --- */
.step-anim__avatar {
  fill: var(--color-primary);
}

.step-anim__avatar-person {
  fill: var(--color-surface);
}

.step-anim__bar {
  fill: var(--color-stroke);
}

.step-anim__bar--strong {
  fill: var(--color-stroke-strong);
}

.step-anim__field {
  fill: var(--color-surface-soft);
  stroke: var(--color-stroke-strong);
  stroke-width: 1.2;
}

.step-anim__field-pin {
  fill: var(--step-orange);
}

.step-anim__typed {
  fill: var(--color-text-muted);
  transform-box: fill-box;
  transform-origin: left center;
  animation: step-typed var(--step-loop) infinite;
}

.step-anim__knob {
  fill: var(--color-primary);
  animation: step-knob var(--step-loop) infinite;
}

.step-anim__toggle-label {
  fill: var(--color-stroke-strong);
}

.step-anim__toggle-label--left {
  animation: step-label-left var(--step-loop) infinite;
}

.step-anim__toggle-label--right {
  fill: var(--color-surface);
  animation: step-label-right var(--step-loop) infinite;
}

.step-anim__track,
.step-anim__track-fill {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
}

.step-anim__track {
  stroke: var(--color-stroke);
}

.step-anim__track-fill {
  stroke: var(--color-primary);
  stroke-dasharray: 100;
  stroke-dashoffset: 35;
  animation: step-track var(--step-loop) infinite;
}

.step-anim__thumb {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 2.4;
  transform: translateX(45.5px);
  animation: step-thumb var(--step-loop) infinite;
}

.step-anim__map {
  fill: var(--color-surface-soft);
}

.step-anim__map-frame {
  fill: none;
  stroke: var(--color-stroke-strong);
  stroke-width: 1.4;
}

.step-anim__lots rect {
  fill: #dbe7fb;
}

.step-anim__green {
  fill: #dff3e7;
}

.step-anim__tree {
  fill: #9fd6b7;
}

.step-anim__streets path {
  fill: none;
  stroke: var(--color-surface);
  stroke-width: 8;
}

.step-anim__house {
  fill: var(--color-surface);
  stroke: var(--color-stroke-strong);
  stroke-width: 1.2;
}

.step-anim__house-ridge {
  stroke: var(--color-stroke-strong);
  stroke-width: 1.2;
  stroke-linecap: round;
}

.step-anim__pin-body {
  fill: var(--step-orange);
  stroke: var(--color-surface);
  stroke-width: 1.5;
  stroke-linejoin: round;
}

.step-anim__pin-body--campus {
  fill: var(--color-primary);
}

.step-anim__pin-disc {
  fill: var(--color-surface);
}

.step-anim__pin-person {
  fill: var(--step-orange);
}

.step-anim__pin-shadow {
  fill: var(--color-text);
  opacity: 0.2;
  animation: step-shadow var(--step-loop) infinite;
}

.step-anim__ripple {
  fill: none;
  stroke: var(--step-orange);
  stroke-width: 2;
  opacity: 0;
  animation: step-ripple var(--step-loop) infinite;
}

.step-anim__drop {
  animation: step-drop var(--step-loop) infinite;
}

@keyframes step-typed {
  0%, 4% { transform: scaleX(0); opacity: 1; animation-timing-function: steps(8, end); }
  24%, 92% { transform: scaleX(1); opacity: 1; }
  100% { transform: scaleX(1); opacity: 0; }
}

@keyframes step-drop {
  0%, 24% { transform: translateY(-70px); opacity: 0; animation-timing-function: ease-in; }
  27% { opacity: 1; }
  36% { transform: translateY(0); animation-timing-function: ease-out; }
  40% { transform: translateY(-7px); animation-timing-function: ease-in; }
  44%, 92% { transform: translateY(0); opacity: 1; }
  100% { transform: translateY(0); opacity: 0; }
}

@keyframes step-shadow {
  0%, 24% { transform: scale(0.3); opacity: 0; }
  36%, 92% { transform: scale(1); opacity: 0.2; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes step-ripple {
  0%, 36% { transform: scale(0.2); opacity: 0; }
  37% { transform: scale(0.2); opacity: 0.8; }
  56%, 100% { transform: scale(1.2); opacity: 0; }
}

@keyframes step-knob {
  0%, 50% { transform: translateX(0); animation-timing-function: cubic-bezier(0.5, 0, 0.2, 1.3); }
  58%, 94% { transform: translateX(38px); }
  100% { transform: translateX(0); }
}

@keyframes step-label-left {
  0%, 52% { fill: var(--color-surface); }
  58%, 94% { fill: var(--color-stroke-strong); }
  100% { fill: var(--color-surface); }
}

@keyframes step-label-right {
  0%, 52% { fill: var(--color-stroke-strong); }
  58%, 94% { fill: var(--color-surface); }
  100% { fill: var(--color-stroke-strong); }
}

@keyframes step-thumb {
  0%, 64% { transform: translateX(14px); animation-timing-function: ease-in-out; }
  76%, 94% { transform: translateX(45.5px); }
  100% { transform: translateX(14px); }
}

@keyframes step-track {
  0%, 64% { stroke-dashoffset: 80; animation-timing-function: ease-in-out; }
  76%, 94% { stroke-dashoffset: 35; }
  100% { stroke-dashoffset: 80; }
}

/* --- Covoiturage --- */
.step-anim__route-base,
.step-anim__route {
  fill: none;
  stroke-linecap: round;
}

.step-anim__route-base {
  stroke: var(--color-surface);
  stroke-width: 11;
}

.step-anim__route {
  stroke: var(--color-primary);
  stroke-width: 5;
  stroke-dasharray: 100;
  stroke-dashoffset: 0;
  animation: step-route var(--step-loop) infinite;
}

.step-anim__origin {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 2.6;
}

.step-anim__campus-glyph {
  fill: var(--color-surface);
}

.step-anim__arrive {
  fill: var(--color-primary);
  opacity: 0;
  transform-box: fill-box;
  transform-origin: center;
  animation: step-arrive var(--step-loop) infinite;
}

.step-anim__rider--1 { animation: step-rider-1 var(--step-loop) infinite; }
.step-anim__rider--2 { animation: step-rider-2 var(--step-loop) infinite; }

.step-anim__car {
  offset-path: path("M30 98 C60 98 62 60 96 58 C132 56 136 92 170 84 C192 79 200 58 204 44");
  offset-rotate: auto;
  offset-distance: 55%;
  animation: step-car var(--step-loop) infinite;
}

.step-anim__car-shadow {
  fill: var(--color-text);
  opacity: 0.2;
}

.step-anim__car-body {
  fill: var(--color-surface);
  stroke: var(--color-text);
  stroke-width: 1.3;
}

.step-anim__car-glass {
  fill: var(--color-text);
}

.step-anim__seat--driver {
  fill: var(--color-primary);
}

.step-anim__seat--rider {
  fill: var(--step-orange);
}

.step-anim__seat--empty {
  fill: var(--color-surface-soft);
  stroke: var(--color-stroke-strong);
  stroke-width: 1.2;
  stroke-dasharray: 2.6 2.6;
}

.step-anim__seat-person {
  fill: var(--color-surface);
}

.step-anim__boarded {
  transform: scale(0);
}

.step-anim__boarded--1 { animation: step-board-1 var(--step-loop) infinite; }
.step-anim__boarded--2 { animation: step-board-2 var(--step-loop) infinite; }

.step-anim__check--trip {
  animation-name: step-check-trip;
}

@keyframes step-car {
  0% { offset-distance: 0%; opacity: 0; }
  4% { offset-distance: 0%; opacity: 1; animation-timing-function: ease-in-out; }
  24%, 32% { offset-distance: 37%; animation-timing-function: ease-in-out; }
  48%, 56% { offset-distance: 74.5%; animation-timing-function: ease-in-out; }
  70% { offset-distance: 97%; }
  92% { offset-distance: 97%; opacity: 1; }
  100% { offset-distance: 97%; opacity: 0; }
}

@keyframes step-route {
  0%, 4% { stroke-dashoffset: 100; opacity: 1; animation-timing-function: ease-in-out; }
  24%, 32% { stroke-dashoffset: 63; animation-timing-function: ease-in-out; }
  48%, 56% { stroke-dashoffset: 25.5; animation-timing-function: ease-in-out; }
  70% { stroke-dashoffset: 0; }
  92% { stroke-dashoffset: 0; opacity: 1; }
  100% { stroke-dashoffset: 0; opacity: 0; }
}

@keyframes step-rider-1 {
  0%, 25% { transform: translateY(0) scale(1); opacity: 1; animation-timing-function: ease-out; }
  28% { transform: translateY(-6px) scale(1); opacity: 1; animation-timing-function: ease-in; }
  31%, 94% { transform: translateY(0) scale(0); opacity: 0; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes step-rider-2 {
  0%, 49% { transform: translateY(0) scale(1); opacity: 1; animation-timing-function: ease-out; }
  52% { transform: translateY(-6px) scale(1); opacity: 1; animation-timing-function: ease-in; }
  55%, 94% { transform: translateY(0) scale(0); opacity: 0; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes step-board-1 {
  0%, 30% { transform: scale(0); opacity: 1; }
  33% { transform: scale(1.2); }
  35%, 92% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes step-board-2 {
  0%, 54% { transform: scale(0); opacity: 1; }
  57% { transform: scale(1.2); }
  59%, 92% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes step-check-trip {
  0%, 70% { transform: scale(0); opacity: 1; }
  74% { transform: scale(1.2); }
  77%, 92% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes step-arrive {
  0%, 69.9% { transform: scale(0.2); opacity: 0; }
  70% { transform: scale(0.2); opacity: 0.3; }
  82%, 100% { transform: scale(1.3); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .step-anim * {
    animation: none !important;
  }

  .step-anim__check,
  .step-anim__boarded {
    transform: scale(1);
  }

  .step-anim__data {
    opacity: 0;
  }
}
</style>

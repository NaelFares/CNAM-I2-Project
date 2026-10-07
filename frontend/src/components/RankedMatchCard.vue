<template>
  <article
    class="ranked-match-card"
    :class="[`ranked-match-card--${tone}`, { 'is-selected': selected }]"
    :aria-current="selected ? 'true' : undefined"
  >
    <div class="ranked-match-card__heading">
      <span class="ranked-match-card__medal" :aria-label="medalLabel">{{ rank }}</span>
      <strong>{{ match.score }} %</strong>
      <button
        type="button"
        :class="selected ? 'ranked-match-card__selected' : 'ranked-match-card__action'"
        :aria-pressed="selected"
        @click="$emit('focus')"
      >
        {{ selected ? "Affiché sur la carte" : "Voir sur la carte" }}
      </button>
    </div>

    <div class="ranked-match-card__people">
      <div class="ranked-match-card__person">
        <span class="ranked-match-card__avatar">{{ initials(match.driver_name) }}</span>
        <span>
          <small>Conducteur</small>
          <strong>{{ match.driver_name }}</strong>
        </span>
      </div>
      <ArrowRight class="ranked-match-card__arrow" aria-hidden="true" />
      <div class="ranked-match-card__person">
        <span class="ranked-match-card__avatar ranked-match-card__avatar--passenger">{{ initials(match.passenger_name) }}</span>
        <span>
          <small>Passager</small>
          <strong>{{ match.passenger_name }}</strong>
        </span>
      </div>
    </div>

    <div class="ranked-match-card__details">
      <span><Clock3 aria-hidden="true" /> Départ {{ formattedDeparture }}</span>
      <span><Route aria-hidden="true" /> +{{ formattedDetour }} min de détour</span>
      <span><MapPin aria-hidden="true" /> {{ formattedDistance }} km</span>
    </div>

    <div class="ranked-match-card__footer">
      <span v-if="availableSeats !== null" class="ranked-match-card__seats" :class="{ 'is-low': availableSeats === 1 }">
        <UsersRound aria-hidden="true" />
        {{ seatsLabel }}
      </span>
      <button
        type="button"
        class="btn-primary ranked-match-card__choose"
        :disabled="busy || availableSeats === 0 || match.already_selected"
        @click="$emit('choose')"
      >
        <LoaderCircle v-if="busy" class="h-4 w-4 animate-spin" aria-hidden="true" />
        <CircleCheckBig v-else class="h-4 w-4" aria-hidden="true" />
        {{ match.already_selected ? "Déjà sélectionné" : "Choisir ce trajet" }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import { ArrowRight, CircleCheckBig, Clock3, LoaderCircle, MapPin, Route, UsersRound } from "lucide-vue-next";

const props = defineProps({
  match: { type: Object, required: true },
  rank: { type: Number, required: true },
  selected: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
});

defineEmits(["focus", "choose"]);

const tone = computed(() => ({ 1: "gold", 2: "silver", 3: "bronze" }[props.rank] || "standard"));
const medalLabel = computed(() => ({ 1: "Classement or", 2: "Classement argent", 3: "Classement bronze" }[props.rank] || `Rang ${props.rank}`));
const formattedDeparture = computed(() => {
  const value = String(props.match.ride_time || "");
  if (!value) return "Horaire non défini";
  const date = new Date(value.replace(" ", "T"));
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
});
const formattedDetour = computed(() => Number(props.match.extra_time_min || 0).toFixed(1));
const formattedDistance = computed(() => Number(props.match.distance_km || 0).toFixed(1));
const availableSeats = computed(() => {
  const value = Number(props.match.available_seats ?? props.match.car_seats);
  return Number.isFinite(value) ? Math.max(0, value) : null;
});
const seatsLabel = computed(() => {
  if (availableSeats.value === 0) return "Complet";
  return `${availableSeats.value} place${availableSeats.value > 1 ? "s" : ""} restante${availableSeats.value > 1 ? "s" : ""}`;
});

function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}
</script>

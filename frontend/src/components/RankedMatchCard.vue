<template>
  <button
    type="button"
    class="ranked-match-card"
    :class="[`ranked-match-card--${tone}`, { 'is-selected': selected }]"
    :aria-pressed="selected"
    @click="$emit('select')"
  >
    <div class="ranked-match-card__heading">
      <span class="ranked-match-card__medal" :aria-label="medalLabel">{{ rank }}</span>
      <strong>{{ match.score }} %</strong>
      <span v-if="selected" class="ranked-match-card__selected">Trajet sélectionné</span>
      <span v-else class="ranked-match-card__action">Voir sur la carte</span>
    </div>

    <div class="ranked-match-card__people">
      <div class="ranked-match-card__person">
        <span class="ranked-match-card__avatar">{{ initials(match.driver_name) }}</span>
        <span>
          <small>Conducteur</small>
          <strong>{{ match.driver_name }}</strong>
        </span>
      </div>
      <span class="ranked-match-card__arrow" aria-hidden="true">→</span>
      <div class="ranked-match-card__person">
        <span class="ranked-match-card__avatar ranked-match-card__avatar--passenger">{{ initials(match.passenger_name) }}</span>
        <span>
          <small>Passager</small>
          <strong>{{ match.passenger_name }}</strong>
        </span>
      </div>
    </div>

    <div class="ranked-match-card__details">
      <span><Clock3 aria-hidden="true" /> Départ {{ formattedTime }}</span>
      <span><Route aria-hidden="true" /> +{{ formattedDetour }} min de détour</span>
      <span><MapPin aria-hidden="true" /> {{ formattedDistance }} km</span>
    </div>
  </button>
</template>

<script setup>
import { computed } from "vue";
import { Clock3, MapPin, Route } from "lucide-vue-next";

const props = defineProps({
  match: { type: Object, required: true },
  rank: { type: Number, required: true },
  selected: { type: Boolean, default: false },
});

defineEmits(["select"]);

const tone = computed(() => ({ 1: "gold", 2: "silver", 3: "bronze" }[props.rank] || "standard"));
const medalLabel = computed(() => ({ 1: "Classement or", 2: "Classement argent", 3: "Classement bronze" }[props.rank] || `Rang ${props.rank}`));
const formattedTime = computed(() => {
  const value = String(props.match.ride_time || "");
  return value.includes(" ") ? value.split(" ").at(-1) : value;
});
const formattedDetour = computed(() => Number(props.match.extra_time_min || 0).toFixed(1));
const formattedDistance = computed(() => Number(props.match.distance_km || 0).toFixed(1));

function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}
</script>

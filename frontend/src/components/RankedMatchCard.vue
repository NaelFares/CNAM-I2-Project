<template>
  <article
    class="match-card"
    :class="{ 'is-selected': selected }"
    :aria-current="selected ? 'true' : undefined"
    @click="$emit('focus')"
  >
    <div class="flex items-start gap-3">
      <span class="match-card__rank" :class="`match-card__rank--${tone}`" :aria-label="`Choix numéro ${rank}`">{{ rank }}</span>
      <Avatar :name="match.driver_name" :photo-url="match.driver_photo_url" size="md" />
      <div class="min-w-0 flex-1">
        <p class="card-title truncate">{{ match.driver_name }}</p>
        <div class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span v-if="match.driver_rating_count" class="inline-flex items-center gap-1 text-[0.8125rem] font-semibold text-slate-700">
            <Star class="h-3.5 w-3.5 fill-amber-400 text-amber-400" aria-hidden="true" />
            {{ formatRating(match.driver_rating_average) }}
            <span class="font-normal text-slate-500">({{ match.driver_rating_count }})</span>
          </span>
          <TierBadge :tier="{ tier_key: match.driver_tier_key, tier_label: match.driver_tier_label }" />
        </div>
      </div>
      <DirectionBadge :ride-type="match.ride_type" />
    </div>

    <dl class="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-[0.8125rem] sm:grid-cols-3">
      <div class="flex items-center gap-1.5 text-slate-700">
        <Clock3 class="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
        <dt class="sr-only">{{ timeLabel }}</dt>
        <dd>{{ timeLabel }} {{ formatTime(rideDate) }}</dd>
      </div>
      <div v-if="match.passage_time" class="flex items-center gap-1.5 text-slate-700">
        <MapPin class="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
        <dt class="sr-only">Passage</dt>
        <dd>{{ passageLabel(match) }}</dd>
      </div>
      <div class="flex items-center gap-1.5 text-slate-700">
        <Route class="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
        <dt class="sr-only">Détour</dt>
        <dd>+{{ formatMinutes(match.extra_time_min) }}</dd>
      </div>
    </dl>

    <ul v-if="ambiance.length" class="mt-3 flex flex-wrap gap-1.5" aria-label="Ambiance du trajet">
      <li v-for="label in ambiance" :key="label" class="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
        {{ label }}
      </li>
    </ul>

    <div class="mt-3 flex items-center justify-between gap-3 border-t border-slate-100 pt-3">
      <span
        v-if="availableSeats !== null"
        class="inline-flex items-center gap-1.5 text-[0.8125rem] font-semibold"
        :class="availableSeats <= 1 ? 'text-warning' : 'text-success'"
      >
        <UsersRound class="h-4 w-4" aria-hidden="true" />
        {{ seatsLabel }}
      </span>
      <Button
        size="sm"
        :disabled="busy || availableSeats === 0 || match.already_selected"
        @click.stop="$emit('choose')"
      >
        <LoaderCircle v-if="busy" class="h-4 w-4 animate-spin" aria-hidden="true" />
        <Check v-else-if="match.already_selected" class="h-4 w-4" aria-hidden="true" />
        {{ match.already_selected ? "Déjà demandé" : "Choisir" }}
        <ChevronRight v-if="!busy && !match.already_selected" class="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import { Check, ChevronRight, Clock3, LoaderCircle, MapPin, Route, Star, UsersRound } from "lucide-vue-next";

import { Avatar, Button, DirectionBadge, TierBadge } from "./ui";
import { isOutbound } from "../lib/direction";
import { formatMinutes, formatTime } from "../lib/format";
import { tripPreferenceBadges } from "../lib/preferences";
import { passageLabel } from "../lib/week";

const props = defineProps({
  match: { type: Object, required: true },
  rank: { type: Number, required: true },
  selected: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
});

defineEmits(["focus", "choose"]);

const tone = computed(() => ({ 1: "gold", 2: "silver", 3: "bronze" }[props.rank] || "standard"));
// L'heure du conducteur est son arrivee a l'aller, son depart au retour.
const timeLabel = computed(() => (isOutbound(props.match.ride_type) ? "Arrivée" : "Départ"));
const rideDate = computed(() => String(props.match.ride_time || "").replace(" ", "T"));
// Ambiance de la voiture : ce sont les preferences du conducteur qui s'appliquent.
const ambiance = computed(() =>
  tripPreferenceBadges({
    music_preference: props.match.driver_music_preference,
    music_genres: props.match.driver_music_genres,
    smoking_preference: props.match.driver_smoking_preference,
  }),
);
const availableSeats = computed(() => {
  const value = Number(props.match.available_seats ?? props.match.car_seats);
  return Number.isFinite(value) ? Math.max(0, value) : null;
});
const seatsLabel = computed(() => {
  if (availableSeats.value === 0) return "Complet";
  return `${availableSeats.value} place${availableSeats.value > 1 ? "s" : ""} libre${availableSeats.value > 1 ? "s" : ""}`;
});

function formatRating(value) {
  return Number(value || 0).toLocaleString("fr-FR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}
</script>

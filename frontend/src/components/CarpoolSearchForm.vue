<template>
  <Card class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="segmented" role="tablist" aria-label="Que rechercher ?">
        <button type="button" role="tab" :aria-selected="scope === 'week'" @click="scope = 'week'">
          <CalendarDays class="h-4 w-4" aria-hidden="true" />
          Ma semaine de cours
        </button>
        <button type="button" role="tab" :aria-selected="scope === 'trip'" @click="scope = 'trip'">
          <MapPinned class="h-4 w-4" aria-hidden="true" />
          Un trajet précis
        </button>
      </div>
    </div>

    <!-- Toute la semaine : un aller et un retour par jour de cours. -->
    <div v-if="scope === 'week'" class="grid gap-4 md:grid-cols-[minmax(0,240px)_minmax(0,1fr)] md:items-end">
      <div>
        <label for="search-week" class="mb-1.5 block text-sm font-medium text-slate-700">Semaine</label>
        <input id="search-week" v-model="weekDate" type="date" class="input" />
      </div>
      <p class="muted flex items-center gap-2 md:pb-2.5">
        <Info class="h-4 w-4 shrink-0" aria-hidden="true" />
        Un aller et un retour pour chaque jour de cours de votre planning, du {{ weekDays[0]?.label }} au {{ weekDays[4]?.label }}.
      </p>
    </div>

    <!-- Un trajet ponctuel : adresses pre-remplies depuis le profil. -->
    <template v-else>
      <div class="segmented" role="radiogroup" aria-label="Sens du trajet">
        <button type="button" role="radio" :aria-checked="rideType === 'to_campus'" :aria-pressed="rideType === 'to_campus'" @click="rideType = 'to_campus'">
          <School class="h-4 w-4 text-outbound" aria-hidden="true" />
          Aller · vers le campus
        </button>
        <button type="button" role="radio" :aria-checked="rideType === 'from_campus'" :aria-pressed="rideType === 'from_campus'" @click="rideType = 'from_campus'">
          <House class="h-4 w-4 text-return" aria-hidden="true" />
          Retour · vers la maison
        </button>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <AddressField :target="origin" label="Départ" :icon="CircleDot" />
        <AddressField :target="destination" label="Arrivée" :icon="MapPin" />
      </div>

      <div class="max-w-xs">
        <!-- A l'aller on vise une heure d'arrivee (debut du cours), au
             retour une heure de depart (fin du cours) : c'est ce que compare
             le matching. -->
        <label for="search-time" class="mb-1.5 block text-sm font-medium text-slate-700">
          {{ rideType === "to_campus" ? "Arriver avant" : "Partir à partir de" }}
        </label>
        <input id="search-time" v-model="rideTimeLocal" type="datetime-local" class="input" />
      </div>
    </template>

    <div class="flex flex-col-reverse gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
      <label v-if="ladiesOnlyAvailable" class="inline-flex items-center gap-2 text-sm text-slate-700">
        <input v-model="ladiesOnly" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
        <Venus class="h-4 w-4 text-pink-600" aria-hidden="true" />
        Uniquement des conductrices
      </label>
      <span v-else></span>
      <Button :disabled="app.loading || !canSearch" @click="onSubmit">
        <Search class="h-4 w-4" aria-hidden="true" />
        Rechercher
      </Button>
    </div>
  </Card>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  CalendarDays,
  CircleDot,
  House,
  Info,
  MapPin,
  MapPinned,
  School,
  Search,
  Venus,
} from "lucide-vue-next";

import AddressField from "./AddressField.vue";
import { canUseLadiesOnly } from "../lib/gender";
import { localDateIso, mondayIso, nextUpcomingEvent, schoolWeekDays } from "../lib/week";
import { useAppStore } from "../stores/app";
import { Button, Card } from "./ui";

const app = useAppStore();
const emit = defineEmits(["search"]);

// "week" : tous les trajets de cours d'une semaine ; "trip" : un trajet ponctuel.
const scope = ref("week");
const origin = reactive({ address: "", lat: null, lon: null, placeLabel: "", confirmed: true });
const destination = reactive({ address: "", lat: null, lon: null, placeLabel: "", confirmed: true });
const rideType = ref("to_campus");
const ladiesOnly = ref(false);
const weekDate = ref(localDateIso());
const weekStart = computed(() => mondayIso(weekDate.value));
const weekDays = computed(() => schoolWeekDays(weekStart.value));

const ladiesOnlyAvailable = computed(() => canUseLadiesOnly(app.profile));

function nextQuarterHour() {
  const date = new Date();
  date.setMinutes(Math.ceil(date.getMinutes() / 15) * 15, 0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

const rideTimeLocal = ref(nextQuarterHour());

const canSearch = computed(() => {
  if (scope.value === "week") return Boolean(weekStart.value);
  return Boolean(origin.address.trim() && destination.address.trim() && origin.lat != null && destination.lat != null);
});

// Le sens du trajet inverse depart et arrivee : domicile -> ecole a l'aller.
function fillAddresses() {
  const p = app.profile;
  if (!p) return;
  const home = { address: p.start_address || "", lat: p.start_lat ?? null, lon: p.start_lon ?? null };
  const school = { address: p.school_address || "", lat: p.school_lat ?? null, lon: p.school_lon ?? null };
  const [from, to] = rideType.value === "to_campus" ? [home, school] : [school, home];
  Object.assign(origin, from, { confirmed: true });
  Object.assign(destination, to, { confirmed: true });
}

onMounted(async () => {
  if (!app.profile) await app.loadProfile();
  // Semaine et heure pre-remplies : celles du prochain cours, quand il y en a un.
  if (!app.events.length) await app.loadScheduleEvents();
  const nextEvent = nextUpcomingEvent(app.events);
  if (nextEvent) {
    weekDate.value = String(nextEvent.start_time).slice(0, 10);
    rideTimeLocal.value = String(nextEvent.start_time).slice(0, 16);
  }
  fillAddresses();
});

function onSubmit() {
  // La case n'est affichee qu'aux utilisatrices, mais on ne se fie pas au
  // rendu : le flag est neutralise si le profil ne le permet pas.
  const ladies = ladiesOnlyAvailable.value && ladiesOnly.value;
  if (scope.value === "week") {
    emit("search", { scope: "week", weekStart: weekStart.value, ladiesOnly: ladies });
    return;
  }
  emit("search", {
    scope: "trip",
    originLat: origin.lat,
    originLon: origin.lon,
    destLat: destination.lat,
    destLon: destination.lon,
    rideTime: rideTimeLocal.value,
    rideType: rideType.value,
    ladiesOnly: ladies,
  });
}

// Changer de sens echange depart et arrivee.
watch(rideType, () => {
  const tmp = { address: origin.address, lat: origin.lat, lon: origin.lon };
  Object.assign(origin, { address: destination.address, lat: destination.lat, lon: destination.lon });
  Object.assign(destination, tmp);
});
</script>

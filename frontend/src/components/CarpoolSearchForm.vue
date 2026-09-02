<template>
  <Card class="space-y-4">
    <div class="grid gap-4 md:grid-cols-2">
      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700">Départ</label>
        <Input v-model="origin.address" placeholder="Adresse de départ…" @input="originAuto.onInput">
          <template #icon><MapPin class="h-4 w-4" /></template>
        </Input>
        <ul v-if="originAuto.suggestions.value.length" class="mt-2 max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
          <li v-for="item in originAuto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
            <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-primary-soft" @click="originAuto.select(item)">
              <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
              <div class="text-xs text-slate-500">{{ item.place_label }}</div>
            </button>
          </li>
        </ul>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700">Arrivée</label>
        <Input v-model="destination.address" placeholder="Adresse d'arrivée…" @input="destinationAuto.onInput">
          <template #icon><School class="h-4 w-4" /></template>
        </Input>
        <ul v-if="destinationAuto.suggestions.value.length" class="mt-2 max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
          <li v-for="item in destinationAuto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
            <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-primary-soft" @click="destinationAuto.select(item)">
              <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
              <div class="text-xs text-slate-500">{{ item.place_label }}</div>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700">Sens du trajet</label>
        <div class="flex gap-2">
          <Button
            type="button"
            :variant="rideType === 'to_campus' ? 'primary' : 'secondary'"
            class="flex-1"
            @click="rideType = 'to_campus'"
          >
            <ArrowRight class="h-4 w-4" />
            Aller au campus
          </Button>
          <Button
            type="button"
            :variant="rideType === 'from_campus' ? 'primary' : 'secondary'"
            class="flex-1"
            @click="rideType = 'from_campus'"
          >
            <ArrowLeft class="h-4 w-4" />
            Retour du campus
          </Button>
        </div>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700">Heure</label>
        <input v-model="rideTimeLocal" type="datetime-local" class="input" />
      </div>
    </div>

    <Button :disabled="app.loading || !canSearch" @click="onSubmit">
      <UsersRound class="h-4 w-4" />
      Rechercher un covoiturage
    </Button>
  </Card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ArrowLeft, ArrowRight, MapPin, School, UsersRound } from "lucide-vue-next";

import { useAddressAutocomplete } from "../composables/useAddressAutocomplete";
import { useAppStore } from "../stores/app";
import { Button, Card, Input } from "./ui";

const app = useAppStore();
const emit = defineEmits(["search"]);

const origin = reactive({ address: "", lat: 46.603354, lon: 1.888334, placeLabel: "" });
const destination = reactive({ address: "", lat: 46.603354, lon: 1.888334, placeLabel: "" });
const originAuto = useAddressAutocomplete(origin);
const destinationAuto = useAddressAutocomplete(destination);

const rideType = ref("to_campus");

function nextQuarterHour() {
  const date = new Date();
  date.setMinutes(Math.ceil(date.getMinutes() / 15) * 15, 0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

const rideTimeLocal = ref(nextQuarterHour());

const canSearch = computed(() => origin.address.trim() && destination.address.trim());

onMounted(async () => {
  if (!app.profile) {
    await app.loadProfile();
  }
  if (app.profile) {
    origin.address = app.profile.start_address || "";
    origin.lat = app.profile.start_lat || origin.lat;
    origin.lon = app.profile.start_lon || origin.lon;
    destination.address = app.profile.school_address || "";
    destination.lat = app.profile.school_lat || destination.lat;
    destination.lon = app.profile.school_lon || destination.lon;
  }
});

function onSubmit() {
  emit("search", {
    originLat: origin.lat,
    originLon: origin.lon,
    destLat: destination.lat,
    destLon: destination.lon,
    rideTime: rideTimeLocal.value,
    rideType: rideType.value,
  });
}
</script>

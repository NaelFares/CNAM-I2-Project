<template>
  <Card class="space-y-5">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-slate-900">Proposer un trajet</h2>
        <p class="text-sm text-slate-600">
          Les autres étudiants pourront vous demander une place.
        </p>
      </div>
      <button
        type="button"
        class="rounded-full p-1.5 text-slate-500 hover:bg-slate-100"
        aria-label="Fermer"
        @click="$emit('close')"
      >
        <X class="h-5 w-5" />
      </button>
    </div>

    <!-- 1. Le sens : la question la plus simple d'abord -->
    <fieldset>
      <legend class="mb-2 text-sm font-semibold text-slate-700">Où allez-vous ?</legend>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="option in DIRECTIONS"
          :key="option.value"
          type="button"
          :class="[
            'flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm font-bold transition',
            rideType === option.value
              ? 'border-blue-700 bg-blue-50 text-blue-800'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
          ]"
          @click="setDirection(option.value)"
        >
          <component :is="option.icon" class="h-4 w-4" />
          {{ option.label }}
        </button>
      </div>
    </fieldset>

    <!-- 2. Les adresses, pre-remplies depuis le profil -->
    <div class="grid gap-4 md:grid-cols-2">
      <AddressField :target="origin" label="Départ" :icon="MapPin" />
      <AddressField :target="destination" label="Arrivée" :icon="Flag" />
    </div>

    <!-- 3. Quand : date et heure separees, plus lisibles qu'un seul champ -->
    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700" for="offer-date">Jour</label>
        <input id="offer-date" v-model="date" type="date" :min="today" class="input" />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-semibold text-slate-700" for="offer-time">{{ rideType === "to_campus" ? "Heure d'arrivée" : "Heure de départ" }}</label>
        <input id="offer-time" v-model="time" type="time" step="300" class="input" />
      </div>
    </div>

    <p class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
      <UsersRound class="h-4 w-4 shrink-0 text-blue-700" />
      Vous proposez {{ seats }} place{{ seats > 1 ? "s" : "" }}.
      <RouterLink to="/profile" class="ml-auto font-semibold text-blue-700 hover:underline">Modifier</RouterLink>
    </p>

    <!-- Ce qui manque encore, dit simplement, plutot qu'un bouton grise muet -->
    <p v-if="missing" class="text-sm text-amber-700">{{ missing }}</p>

    <div class="flex flex-wrap justify-end gap-2">
      <Button variant="secondary" @click="$emit('close')">Annuler</Button>
      <Button :disabled="Boolean(missing) || app.offerSaving" @click="onSubmit">
        <Check class="h-4 w-4" />
        Proposer ce trajet
      </Button>
    </div>
  </Card>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { Check, Flag, House, MapPin, School, UsersRound, X } from "lucide-vue-next";

import AddressField from "./AddressField.vue";
import { useAppStore } from "../stores/app";
import { localDateIso } from "../lib/week";
import { Button, Card } from "./ui";

const emit = defineEmits(["close", "created"]);
const app = useAppStore();

const DIRECTIONS = [
  { value: "to_campus", label: "Je vais à l'école", icon: School },
  { value: "from_campus", label: "Je rentre de l'école", icon: House },
];

const profile = computed(() => app.profile || {});
const seats = computed(() => profile.value.car_seats || 0);

// Adresses du profil, pour pre-remplir dans le bon sens.
function homeAddress() {
  const p = profile.value;
  return { address: p.start_address || "", lat: p.start_lat, lon: p.start_lon, placeLabel: "", confirmed: Boolean(p.start_address) };
}
function schoolAddress() {
  const p = profile.value;
  return { address: p.school_address || "", lat: p.school_lat, lon: p.school_lon, placeLabel: "", confirmed: Boolean(p.school_address) };
}

const rideType = ref("to_campus");
const origin = reactive(homeAddress());
const destination = reactive(schoolAddress());

function setDirection(value) {
  if (value === rideType.value) return;
  rideType.value = value;
  // Changer de sens inverse depart et arrivee : c'est presque toujours ce
  // que l'on veut (domicile -> ecole devient ecole -> domicile).
  const previousOrigin = { ...origin };
  Object.assign(origin, { ...destination });
  Object.assign(destination, previousOrigin);
}

// Par defaut : demain, a 8 h.
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const today = localDateIso();
const date = ref(localDateIso(tomorrow));
const time = ref("08:00");

const missing = computed(() => {
  if (!origin.confirmed || !destination.confirmed) return "Choisissez le départ et l'arrivée dans la liste des adresses.";
  if (!date.value || !time.value) return "Indiquez le jour et l'heure.";
  if (new Date(`${date.value}T${time.value}`) <= new Date()) return "Choisissez une date et une heure à venir.";
  return "";
});

async function onSubmit() {
  if (missing.value) return;
  const ok = await app.createOffer({
    ride_type: rideType.value,
    // Heure locale sans fuseau, comme le reste de l'application.
    ride_time: `${date.value}T${time.value}:00`,
    start_address: origin.address,
    start_lat: origin.lat,
    start_lon: origin.lon,
    end_address: destination.address,
    end_lat: destination.lat,
    end_lon: destination.lon,
  });
  if (ok) emit("created");
}
</script>

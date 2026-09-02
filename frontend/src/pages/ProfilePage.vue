<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mon profil</h1>
      <p class="page-subtitle">Ces informations servent à calculer vos trajets et vos correspondances.</p>
    </header>

    <form class="space-y-5" @submit.prevent="onSubmit">
      <!-- Infos de base -->
      <Card>
        <h2 class="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
          <Info class="h-4 w-4" />
          Informations générales
        </h2>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="md:col-span-2">
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Nom complet</label>
            <Input v-model="form.name" required />
          </div>
          <div class="md:col-span-2">
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
            <Input v-model="form.email" type="email" required />
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Rôle</label>
            <select v-model="form.role" class="input">
              <option value="both">Conducteur et passager</option>
              <option value="driver">Conducteur</option>
              <option value="passenger">Passager</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Tolérance horaire (minutes)</label>
            <Input v-model.number="form.time_tolerance_min" type="number" min="5" max="60" />
          </div>
        </div>
      </Card>

      <!-- Deux cards adresses côte à côte -->
      <div class="grid gap-5 lg:grid-cols-2">

        <!-- Card Domicile -->
        <Card class="space-y-4">
          <h2 class="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
            <MapPin class="h-4 w-4 text-primary" />
            Adresse de départ (domicile)
          </h2>

          <Input v-model="startTarget.address" placeholder="Numéro, rue, ville…" @input="startAuto.onInput">
            <template #icon><MapPin class="h-4 w-4" /></template>
          </Input>

          <ul v-if="startAuto.suggestions.value.length" class="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <li v-for="item in startAuto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
              <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-primary-soft" @click="startAuto.select(item)">
                <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
                <div class="text-xs text-slate-500">{{ item.place_label }}</div>
              </button>
            </li>
          </ul>

          <div class="flex flex-wrap items-center gap-3">
            <Button variant="secondary" @click="startAuto.locate">
              <LocateFixed class="h-4 w-4" />
              Localiser automatiquement
            </Button>
            <Badge v-if="startPlaceLabel" variant="primary">
              <MapPinned class="h-3.5 w-3.5" />
              {{ startPlaceLabel }}
            </Badge>
          </div>

          <button type="button" class="text-sm font-semibold text-primary" @click="showStartMap = !showStartMap">
            {{ showStartMap ? "Masquer la carte" : "Ajuster sur la carte" }}
          </button>
          <div v-if="showStartMap" class="space-y-2">
            <MapPicker :lat="form.start_lat" :lon="form.start_lon" @moved="startAuto.onMapMoved" />
            <p class="text-xs text-slate-500">Cliquez ou faites glisser le marqueur pour affiner la position.</p>
          </div>
        </Card>

        <!-- Card École -->
        <Card class="space-y-4">
          <h2 class="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
            <School class="h-4 w-4 text-success" />
            Adresse de l'école
            <span class="ml-1 text-xs font-normal normal-case text-slate-400">(destination par défaut)</span>
          </h2>

          <Input v-model="schoolTarget.address" placeholder="Nom ou adresse de l'établissement…" @input="schoolAuto.onInput">
            <template #icon><School class="h-4 w-4" /></template>
          </Input>

          <ul v-if="schoolAuto.suggestions.value.length" class="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <li v-for="item in schoolAuto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
              <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-success-soft" @click="schoolAuto.select(item)">
                <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
                <div class="text-xs text-slate-500">{{ item.place_label }}</div>
              </button>
            </li>
          </ul>

          <div class="flex flex-wrap items-center gap-3">
            <Button variant="secondary" @click="schoolAuto.locate">
              <LocateFixed class="h-4 w-4" />
              Localiser automatiquement
            </Button>
            <Badge v-if="schoolPlaceLabel" variant="success">
              <MapPinned class="h-3.5 w-3.5" />
              {{ schoolPlaceLabel }}
            </Badge>
          </div>

          <button type="button" class="text-sm font-semibold text-primary" @click="showSchoolMap = !showSchoolMap">
            {{ showSchoolMap ? "Masquer la carte" : "Ajuster sur la carte" }}
          </button>
          <div v-if="showSchoolMap" class="space-y-2">
            <MapPicker :lat="form.school_lat || 46.603354" :lon="form.school_lon || 1.888334" @moved="schoolAuto.onMapMoved" />
            <p class="text-xs text-slate-500">Cliquez ou faites glisser le marqueur pour affiner la position.</p>
          </div>
        </Card>
      </div>

      <!-- Aperçu du trajet domicile <-> école -->
      <Card padding="responsive">
        <h2 class="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
          <Route class="h-4 w-4 text-primary" />
          Aperçu du trajet domicile ↔ école
        </h2>
        <RouteMap
          :route-geometry="previewRoute.geometry"
          :driver-coords="[form.start_lat, form.start_lon]"
          :dest-coords="[form.school_lat, form.school_lon]"
          :route-label="previewRoute.geometry.length ? `${formattedDuration} · ${previewRoute.distanceKm.toFixed(1)} km` : ''"
        />
        <p class="mt-2 text-xs text-slate-500">
          Recalculé automatiquement à chaque changement d'adresse — non enregistré.
        </p>
      </Card>

      <!-- Bouton de sauvegarde -->
      <div class="flex justify-end">
        <Button type="submit" :disabled="app.loading">
          <Save class="h-4 w-4" />
          Sauvegarder le profil
        </Button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { Info, LocateFixed, MapPin, MapPinned, Route, Save, School } from "lucide-vue-next";

import MapPicker from "../components/MapPicker.vue";
import RouteMap from "../components/RouteMap.vue";
import { Badge, Button, Card, Input } from "../components/ui";
import { getRoutePreview } from "../api/endpoints";
import { useAddressAutocomplete } from "../composables/useAddressAutocomplete";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const app = useAppStore();

const startPlaceLabel = ref("");
const schoolPlaceLabel = ref("");
const showStartMap = ref(false);
const showSchoolMap = ref(false);

const form = reactive({
  name: "",
  email: "",
  role: "both",
  start_address: "",
  start_lat: 46.603354,
  start_lon: 1.888334,
  time_tolerance_min: 15,
  school_address: "",
  school_lat: 0,
  school_lon: 0,
});

const startTarget = reactive({
  address: computed({ get: () => form.start_address, set: (v) => (form.start_address = v) }),
  lat: computed({ get: () => form.start_lat, set: (v) => (form.start_lat = v) }),
  lon: computed({ get: () => form.start_lon, set: (v) => (form.start_lon = v) }),
  placeLabel: startPlaceLabel,
});
const schoolTarget = reactive({
  address: computed({ get: () => form.school_address, set: (v) => (form.school_address = v) }),
  lat: computed({ get: () => form.school_lat, set: (v) => (form.school_lat = v) }),
  lon: computed({ get: () => form.school_lon, set: (v) => (form.school_lon = v) }),
  placeLabel: schoolPlaceLabel,
});

const startAuto = useAddressAutocomplete(startTarget);
const schoolAuto = useAddressAutocomplete(schoolTarget);

const previewRoute = ref({ geometry: [], distanceKm: 0, durationMin: 0 });
let previewTimer = null;

const formattedDuration = computed(() => {
  const minutes = Math.round(previewRoute.value.durationMin);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = String(minutes % 60).padStart(2, "0");
  return `${hours} h ${rest}`;
});

function scheduleRoutePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(async () => {
    try {
      const data = await getRoutePreview({
        start_lat: form.start_lat,
        start_lon: form.start_lon,
        end_lat: form.school_lat,
        end_lon: form.school_lon,
      });
      previewRoute.value = {
        geometry: data.geometry,
        distanceKm: data.distance_m / 1000,
        durationMin: data.duration_s / 60,
      };
    } catch {
      previewRoute.value = { geometry: [], distanceKm: 0, durationMin: 0 };
    }
  }, 300);
}

watch(() => [form.start_lat, form.start_lon, form.school_lat, form.school_lon], scheduleRoutePreview);

onMounted(async () => {
  await app.loadProfile();
  const source = app.profile ?? auth.user;
  if (!source) return;
  form.name = source.name;
  form.email = source.email;
  form.role = source.role;
  form.start_address = source.start_address;
  form.start_lat = source.start_lat || form.start_lat;
  form.start_lon = source.start_lon || form.start_lon;
  form.time_tolerance_min = source.time_tolerance_min;
  form.school_address = source.school_address || "";
  form.school_lat = source.school_lat || 0;
  form.school_lon = source.school_lon || 0;
});

// --- Soumission ---
async function onSubmit() {
  await app.saveProfile({
    name: form.name,
    email: form.email,
    role: form.role,
    start_address: form.start_address,
    start_lat: form.start_lat,
    start_lon: form.start_lon,
    time_tolerance_min: form.time_tolerance_min,
    school_address: form.school_address,
    school_lat: form.school_lat,
    school_lon: form.school_lon,
  });
}
</script>

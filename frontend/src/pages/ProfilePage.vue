<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mon profil</h1>
      <p class="page-subtitle">Ces informations servent à calculer vos trajets et vos correspondances.</p>
    </header>

    <form class="space-y-5" @submit.prevent="onSubmit">
      <!-- Infos de base -->
      <div class="card p-6">
        <h2 class="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
          <Info class="h-4 w-4" />
          Informations générales
        </h2>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="md:col-span-2">
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Nom complet</label>
            <input v-model="form.name" class="input" required />
          </div>
          <div class="md:col-span-2">
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
            <input v-model="form.email" type="email" class="input" required />
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
            <input v-model.number="form.time_tolerance_min" type="number" min="5" max="60" class="input" />
          </div>
        </div>
      </div>

      <!-- Deux cards adresses côte à côte -->
      <div class="grid gap-5 lg:grid-cols-2">

        <!-- Card Domicile -->
        <div class="card p-6 space-y-4">
          <h2 class="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
            <MapPin class="h-4 w-4 text-blue-600" />
            Adresse de départ (domicile)
          </h2>

          <div class="relative">
            <MapPin class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input v-model="form.start_address" class="input input-with-icon" placeholder="Numéro, rue, ville…" @input="onAddressInput" />
          </div>

          <ul v-if="suggestions.length" class="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <li v-for="item in suggestions" :key="`${item.display_name}-${item.lat}`">
              <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-blue-50" @click="selectSuggestion(item)">
                <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
                <div class="text-xs text-slate-500">{{ item.place_label }}</div>
              </button>
            </li>
          </ul>

          <div class="flex flex-wrap items-center gap-3">
            <button type="button" class="btn-secondary" @click="locateAddress">
              <LocateFixed class="h-4 w-4" />
              Localiser automatiquement
            </button>
            <p v-if="placeLabel" class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
              <MapPinned class="h-3.5 w-3.5" />
              {{ placeLabel }}
            </p>
          </div>

          <MapPicker :lat="form.start_lat" :lon="form.start_lon" @moved="onMapMoved" />
          <p class="text-xs text-slate-500">Cliquez ou faites glisser le marqueur pour affiner la position.</p>
        </div>

        <!-- Card École -->
        <div class="card p-6 space-y-4">
          <h2 class="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-500">
            <School class="h-4 w-4 text-emerald-600" />
            Adresse de l'école
            <span class="ml-1 text-xs font-normal normal-case text-slate-400">(destination par défaut)</span>
          </h2>

          <div class="relative">
            <School class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input v-model="form.school_address" class="input input-with-icon" placeholder="Nom ou adresse de l'établissement…" @input="onSchoolInput" />
          </div>

          <ul v-if="schoolSuggestions.length" class="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <li v-for="item in schoolSuggestions" :key="`${item.display_name}-${item.lat}`">
              <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-emerald-50" @click="selectSchoolSuggestion(item)">
                <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
                <div class="text-xs text-slate-500">{{ item.place_label }}</div>
              </button>
            </li>
          </ul>

          <div class="flex flex-wrap items-center gap-3">
            <button type="button" class="btn-secondary" @click="locateSchool">
              <LocateFixed class="h-4 w-4" />
              Localiser automatiquement
            </button>
            <p v-if="schoolPlaceLabel" class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
              <MapPinned class="h-3.5 w-3.5" />
              {{ schoolPlaceLabel }}
            </p>
          </div>

          <MapPicker :lat="form.school_lat || 46.603354" :lon="form.school_lon || 1.888334" @moved="onSchoolMapMoved" />
          <p class="text-xs text-slate-500">Cliquez ou faites glisser le marqueur pour affiner la position.</p>
        </div>
      </div>

      <!-- Bouton de sauvegarde -->
      <div class="flex justify-end">
        <button class="btn-primary" :disabled="app.loading">
          <Save class="h-4 w-4" />
          Sauvegarder le profil
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { Info, LocateFixed, MapPin, MapPinned, Save, School } from "lucide-vue-next";

import MapPicker from "../components/MapPicker.vue";
import { reverseAddress, searchAddress } from "../api/endpoints";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";
import { useFeedbackStore } from "../stores/feedback";

const auth = useAuthStore();
const app = useAppStore();
const feedback = useFeedbackStore();

const suggestions = ref([]);
const placeLabel = ref("");
const schoolSuggestions = ref([]);
const schoolPlaceLabel = ref("");

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

// --- Domicile ---
async function onAddressInput() {
  if (form.start_address.trim().length < 3) { suggestions.value = []; return; }
  try { suggestions.value = await searchAddress(form.start_address.trim()); }
  catch { suggestions.value = []; }
}

function selectSuggestion(item) {
  form.start_address = item.display_name;
  form.start_lat = item.lat;
  form.start_lon = item.lon;
  placeLabel.value = item.place_label;
  suggestions.value = [];
}

async function locateAddress() {
  if (!form.start_address.trim()) { feedback.showInfo("Saisissez d'abord une adresse."); return; }
  try {
    const results = await searchAddress(form.start_address.trim());
    if (!results.length) { feedback.showError("Adresse introuvable."); return; }
    selectSuggestion(results[0]);
    feedback.showSuccess("Adresse localisée sur la carte.");
  } catch { feedback.showError("La recherche d'adresse a échoué."); }
}

async function onMapMoved(lat, lon) {
  form.start_lat = lat;
  form.start_lon = lon;
  const result = await reverseAddress(lat, lon).catch(() => null);
  if (!result) return;
  form.start_address = result.display_name;
  placeLabel.value = result.place_label;
}

// --- École ---
async function onSchoolInput() {
  if (form.school_address.trim().length < 3) { schoolSuggestions.value = []; return; }
  try { schoolSuggestions.value = await searchAddress(form.school_address.trim()); }
  catch { schoolSuggestions.value = []; }
}

function selectSchoolSuggestion(item) {
  form.school_address = item.display_name;
  form.school_lat = item.lat;
  form.school_lon = item.lon;
  schoolPlaceLabel.value = item.place_label;
  schoolSuggestions.value = [];
}

async function locateSchool() {
  if (!form.school_address.trim()) { feedback.showInfo("Saisissez d'abord l'adresse de votre école."); return; }
  try {
    const results = await searchAddress(form.school_address.trim());
    if (!results.length) { feedback.showError("Adresse introuvable."); return; }
    selectSchoolSuggestion(results[0]);
    feedback.showSuccess("École localisée sur la carte.");
  } catch { feedback.showError("La recherche d'adresse a échoué."); }
}

async function onSchoolMapMoved(lat, lon) {
  form.school_lat = lat;
  form.school_lon = lon;
  const result = await reverseAddress(lat, lon).catch(() => null);
  if (!result) return;
  form.school_address = result.display_name;
  schoolPlaceLabel.value = result.place_label;
}

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

<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mon profil</h1>
      <p class="page-subtitle">Ces informations servent à calculer vos trajets et vos correspondances.</p>
    </header>

    <div class="advice-banner">
      Conseil: positionnez précisément le marqueur sur la carte pour améliorer le calcul des distances.
    </div>

    <div class="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
      <div class="card p-6">
        <form class="space-y-4" @submit.prevent="onSubmit">
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

          <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">Adresse de départ</label>
            <div class="relative">
              <MapPin class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input v-model="form.start_address" class="input input-with-icon" @input="onAddressInput" />
            </div>

            <ul v-if="suggestions.length" class="mt-2 max-h-56 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
              <li v-for="item in suggestions" :key="`${item.display_name}-${item.lat}`">
                <button type="button" class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-blue-50" @click="selectSuggestion(item)">
                  <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
                  <div class="text-xs text-slate-500">{{ item.place_label }}</div>
                </button>
              </li>
            </ul>

            <div class="mt-3 flex flex-wrap items-center gap-3">
              <button type="button" class="btn-secondary" @click="locateAddress">
                <LocateFixed class="h-4 w-4" />
                Localiser automatiquement
              </button>
              <span class="text-xs font-medium text-slate-500">Vous pouvez affiner la position manuellement sur la carte.</span>
            </div>

            <p v-if="placeLabel" class="mt-2 inline-flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-700">
              <MapPinned class="h-4 w-4" />
              {{ placeLabel }}
            </p>
          </div>

          <button class="btn-primary" :disabled="app.loading">
            <Save class="h-4 w-4" />
            Sauvegarder le profil
          </button>
        </form>
      </div>

      <aside class="space-y-4">
        <div class="card p-4">
          <h2 class="mb-2 flex items-center gap-2 text-sm font-bold text-slate-800">
            <Info class="h-4 w-4 text-blue-700" />
            Bonnes pratiques
          </h2>
          <ul class="space-y-2 text-sm text-slate-600">
            <li>Adresse la plus précise possible (numéro + rue + ville).</li>
            <li>Tolérance horaire réaliste pour augmenter les matchs.</li>
            <li>Vérifiez le point exact en déplaçant le marqueur.</li>
          </ul>
        </div>

        <div class="card p-3">
          <MapPicker :lat="form.start_lat" :lon="form.start_lon" @moved="onMapMoved" />
          <p class="mt-2 text-xs font-medium text-slate-500">Cliquez ou faites glisser le marqueur pour ajuster le point de départ.</p>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { Info, LocateFixed, MapPin, MapPinned, Save } from "lucide-vue-next";

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

const form = reactive({
  name: "",
  email: "",
  role: "both",
  start_address: "",
  start_lat: 46.603354,
  start_lon: 1.888334,
  time_tolerance_min: 15,
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
});

async function onAddressInput() {
  if (form.start_address.trim().length < 3) {
    suggestions.value = [];
    return;
  }
  try {
    suggestions.value = await searchAddress(form.start_address.trim());
  } catch {
    suggestions.value = [];
  }
}

function selectSuggestion(item) {
  form.start_address = item.display_name;
  form.start_lat = item.lat;
  form.start_lon = item.lon;
  placeLabel.value = item.place_label;
  suggestions.value = [];
}

async function locateAddress() {
  if (!form.start_address.trim()) {
    feedback.showInfo("Saisissez d'abord une adresse avant la localisation.");
    return;
  }
  let results = [];
  try {
    results = await searchAddress(form.start_address.trim());
  } catch {
    feedback.showError("La recherche d'adresse a échoué. Réessayez.");
    return;
  }
  if (!results.length) {
    feedback.showError("Adresse introuvable. Essayez une adresse plus précise.");
    return;
  }
  selectSuggestion(results[0]);
  feedback.showSuccess("Adresse localisée sur la carte.");
}

async function onMapMoved(lat, lon) {
  form.start_lat = lat;
  form.start_lon = lon;
  const result = await reverseAddress(lat, lon).catch(() => null);
  if (!result) return;
  form.start_address = result.display_name;
  placeLabel.value = result.place_label;
}

async function onSubmit() {
  await app.saveProfile({
    name: form.name,
    email: form.email,
    role: form.role,
    start_address: form.start_address,
    start_lat: form.start_lat,
    start_lon: form.start_lon,
    time_tolerance_min: form.time_tolerance_min,
  });
}
</script>

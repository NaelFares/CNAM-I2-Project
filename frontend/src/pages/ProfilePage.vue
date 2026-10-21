<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mon profil</h1>
      <p class="page-subtitle">Ces informations servent à trouver les trajets qui vous correspondent.</p>
    </header>

    <!-- Identite et reputation -->
    <Card class="flex flex-wrap items-center gap-5">
      <!-- Photo de profil : hors du formulaire, elle a son propre endpoint -->
      <div class="relative">
        <Avatar :name="form.name" :photo-url="photoUrl" size="xl" />
        <button
          type="button"
          class="absolute -bottom-1 -right-1 grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-primary text-white shadow"
          :aria-label="photoUrl ? 'Changer la photo' : 'Ajouter une photo'"
          :title="photoUrl ? 'Changer la photo' : 'Ajouter une photo'"
          :disabled="app.loading"
          @click="photoInput?.click()"
        >
          <Camera class="h-4 w-4" aria-hidden="true" />
        </button>
        <input ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onPhotoSelected" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-xl font-bold text-slate-900">{{ form.name || "—" }}</p>
        <p class="muted truncate">{{ form.email }}</p>
        <button v-if="photoUrl" type="button" class="btn-ghost btn-sm -ml-3 mt-1" :disabled="app.loading" @click="onPhotoRemove">
          <Trash2 class="h-4 w-4" aria-hidden="true" />
          Retirer la photo
        </button>
      </div>
    </Card>

    <section class="space-y-3">
      <SectionHeader title="Réputation" />
      <ReputationCard />
    </section>

    <form class="space-y-8" @submit.prevent="onSubmit">
      <!-- Trajet domicile <-> ecole -->
      <section class="space-y-3">
        <SectionHeader title="Mon trajet" subtitle="Domicile et école servent de départ et d'arrivée par défaut." />
        <Card class="space-y-5">
          <div class="grid gap-4 md:grid-cols-2">
            <AddressField :target="startTarget" label="Domicile" :icon="House" placeholder="Numéro, rue, ville…" />
            <AddressField :target="schoolTarget" label="École" :icon="School" placeholder="Nom ou adresse de l'établissement…" />
          </div>

          <div class="overflow-hidden rounded-xl border border-slate-200">
            <MapPicker
              v-if="adjusting"
              :lat="adjusting === 'start' ? form.start_lat : form.school_lat"
              :lon="adjusting === 'start' ? form.start_lon : form.school_lon"
              @moved="onMapMoved"
            />
            <RouteMap
              v-else
              :route-geometry="previewRoute.geometry"
              :driver-coords="[form.start_lat, form.start_lon]"
              :dest-coords="[form.school_lat, form.school_lon]"
              :route-label="previewRoute.geometry.length ? `${previewRoute.estimated ? '≈ ' : ''}${formattedDuration} · ${formattedDistance}` : ''"
              :estimated="previewRoute.estimated"
            />
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <span class="muted mr-auto">
              {{ adjusting ? "Cliquez ou faites glisser le marqueur pour affiner la position." : "Aperçu recalculé à chaque changement d'adresse." }}
            </span>
            <template v-if="!adjusting">
              <Button size="sm" variant="secondary" @click="adjusting = 'start'">
                <Crosshair class="h-4 w-4" aria-hidden="true" />
                Ajuster le domicile
              </Button>
              <Button size="sm" variant="secondary" @click="adjusting = 'school'">
                <Crosshair class="h-4 w-4" aria-hidden="true" />
                Ajuster l'école
              </Button>
            </template>
            <Button v-else size="sm" @click="adjusting = null">
              <Check class="h-4 w-4" aria-hidden="true" />
              Terminé
            </Button>
          </div>

          <div class="max-w-xs">
            <label for="tolerance" class="mb-1.5 block text-sm font-medium text-slate-700">Tolérance horaire</label>
            <div class="relative">
              <Input id="tolerance" v-model.number="form.time_tolerance_min" type="number" min="5" max="60" />
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">min</span>
            </div>
            <p class="muted mt-1">Avance à l'aller, attente au retour : ce que vous acceptez.</p>
          </div>
        </Card>
      </section>

      <!-- Voiture -->
      <section class="space-y-3">
        <SectionHeader title="Ma voiture" subtitle="Facultatif : nécessaire seulement pour proposer des trajets." />
        <Card>
          <div class="segmented" role="radiogroup" aria-label="Places proposées">
            <button type="button" role="radio" :aria-checked="!form.car_seats" :aria-pressed="!form.car_seats" @click="form.car_seats = null">
              Pas de voiture
            </button>
            <button
              v-for="count in [1, 2, 3, 4]"
              :key="count"
              type="button"
              role="radio"
              :aria-checked="Number(form.car_seats) === count"
              :aria-pressed="Number(form.car_seats) === count"
              @click="form.car_seats = count"
            >
              {{ count }} place{{ count > 1 ? "s" : "" }}
            </button>
          </div>
          <p class="muted mt-2">Places passagers, conducteur non compté.</p>
        </Card>
      </section>

      <!-- Informations et preferences -->
      <section class="space-y-3">
        <SectionHeader title="Informations et préférences" />
        <Card class="space-y-5">
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label for="name" class="mb-1.5 block text-sm font-medium text-slate-700">Nom complet</label>
              <Input id="name" v-model="form.name" required />
            </div>
            <div>
              <label for="email" class="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
              <Input id="email" v-model="form.email" type="email" required />
            </div>
            <div>
              <label for="gender" class="mb-1.5 block text-sm font-medium text-slate-700">Sexe</label>
              <select id="gender" v-model="form.gender" required class="input">
                <option v-for="option in GENDER_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </div>
            <div>
              <label for="smoking" class="mb-1.5 block text-sm font-medium text-slate-700">Tabac</label>
              <select id="smoking" v-model="form.smoking_preference" class="input">
                <option v-for="option in SMOKING_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </div>
            <div>
              <label for="music" class="mb-1.5 block text-sm font-medium text-slate-700">Musique</label>
              <select id="music" v-model="form.music_preference" class="input">
                <option v-for="option in MUSIC_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </div>
          </div>

          <!-- Styles : uniquement si la musique est acceptee -->
          <div v-if="showMusicGenres">
            <p class="mb-1.5 text-sm font-medium text-slate-700">
              Styles de musique
              <span class="font-normal text-slate-400">({{ form.music_genres.length }}/{{ MAX_MUSIC_GENRES }}, facultatif)</span>
            </p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="option in MUSIC_GENRE_OPTIONS"
                :key="option.value"
                type="button"
                :disabled="isGenreDisabled(option.value)"
                :aria-pressed="form.music_genres.includes(option.value)"
                :class="[
                  'rounded-full border px-3 py-1 text-sm font-medium transition',
                  form.music_genres.includes(option.value)
                    ? 'border-primary bg-primary-soft text-primary'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                  isGenreDisabled(option.value) ? 'cursor-not-allowed opacity-40' : '',
                ]"
                @click="toggleGenre(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
        </Card>
      </section>

      <!-- Enregistrement : toujours a portee de main -->
      <div class="profile-save-bar">
        <Button type="submit" :disabled="app.loading">
          <Save class="h-4 w-4" aria-hidden="true" />
          Enregistrer
        </Button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { Camera, Check, Crosshair, House, Save, School, Trash2 } from "lucide-vue-next";

import AddressField from "../components/AddressField.vue";
import MapPicker from "../components/MapPicker.vue";
import ReputationCard from "../components/ReputationCard.vue";
import RouteMap from "../components/RouteMap.vue";
import { Avatar, Button, Card, Input, SectionHeader } from "../components/ui";
import { getRoutePreview } from "../api/endpoints";
import { useAddressAutocomplete } from "../composables/useAddressAutocomplete";
import { GENDER_OPTIONS } from "../lib/gender";
import {
  MAX_MUSIC_GENRES,
  MUSIC_GENRE_OPTIONS,
  MUSIC_OPTIONS,
  SMOKING_OPTIONS,
  wantsMusic,
} from "../lib/preferences";
import { useAppStore } from "../stores/app";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const app = useAppStore();

const photoInput = ref(null);
// La photo ne transite pas par `form` : elle a son propre endpoint et le
// store fait foi apres chaque televersement.
const photoUrl = computed(() => app.profile?.photo_url || "");
const showMusicGenres = computed(() => wantsMusic(form.music_preference));

function isGenreDisabled(value) {
  // Plafond atteint : on peut encore decocher, plus ajouter.
  return !form.music_genres.includes(value) && form.music_genres.length >= MAX_MUSIC_GENRES;
}

function toggleGenre(value) {
  const index = form.music_genres.indexOf(value);
  if (index >= 0) {
    form.music_genres.splice(index, 1);
  } else if (form.music_genres.length < MAX_MUSIC_GENRES) {
    form.music_genres.push(value);
  }
}

const startPlaceLabel = ref("");
const schoolPlaceLabel = ref("");
// Adresse en cours d'ajustement sur la carte : "start", "school" ou null.
const adjusting = ref(null);
// Sans adresse connue, la carte s'ouvre sur Toulouse (zone couverte par l'appli).
const DEFAULT_LAT = 43.6045;
const DEFAULT_LON = 1.444;

const form = reactive({
  name: "",
  email: "",
  gender: "autre",
  music_preference: "peu_importe",
  music_genres: [],
  smoking_preference: "peu_importe",
  car_seats: null,
  start_address: "",
  start_lat: DEFAULT_LAT,
  start_lon: DEFAULT_LON,
  time_tolerance_min: 15,
  school_address: "",
  school_lat: DEFAULT_LAT,
  school_lon: DEFAULT_LON,
});

const startTarget = reactive({
  address: computed({ get: () => form.start_address, set: (v) => (form.start_address = v) }),
  lat: computed({ get: () => form.start_lat, set: (v) => (form.start_lat = v) }),
  lon: computed({ get: () => form.start_lon, set: (v) => (form.start_lon = v) }),
  placeLabel: startPlaceLabel,
  confirmed: true,
});
const schoolTarget = reactive({
  address: computed({ get: () => form.school_address, set: (v) => (form.school_address = v) }),
  lat: computed({ get: () => form.school_lat, set: (v) => (form.school_lat = v) }),
  lon: computed({ get: () => form.school_lon, set: (v) => (form.school_lon = v) }),
  placeLabel: schoolPlaceLabel,
  confirmed: true,
});

const startAuto = useAddressAutocomplete(startTarget);
const schoolAuto = useAddressAutocomplete(schoolTarget);

const previewRoute = ref({ geometry: [], distanceKm: 0, durationMin: 0, estimated: false });
let previewTimer = null;

const formattedDuration = computed(() => {
  const minutes = Math.round(previewRoute.value.durationMin);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = String(minutes % 60).padStart(2, "0");
  return `${hours} h ${rest}`;
});

const formattedDistance = computed(() =>
  `${previewRoute.value.distanceKm.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km`,
);

function onMapMoved(lat, lon) {
  (adjusting.value === "start" ? startAuto : schoolAuto).onMapMoved(lat, lon);
}

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
        estimated: Boolean(data.estimated),
      };
    } catch {
      previewRoute.value = { geometry: [], distanceKm: 0, durationMin: 0, estimated: false };
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
  form.gender = source.gender || "autre";
  form.music_preference = source.music_preference || "peu_importe";
  form.music_genres = [...(source.music_genres || [])];
  form.smoking_preference = source.smoking_preference || "peu_importe";
  form.car_seats = source.car_seats ?? null;
  form.start_address = source.start_address;
  form.start_lat = source.start_lat || form.start_lat;
  form.start_lon = source.start_lon || form.start_lon;
  form.time_tolerance_min = source.time_tolerance_min;
  form.school_address = source.school_address || "";
  form.school_lat = source.school_lat || DEFAULT_LAT;
  form.school_lon = source.school_lon || DEFAULT_LON;
});

// --- Photo de profil ---
async function onPhotoSelected(event) {
  const file = event.target.files?.[0];
  // Le champ est remis a zero systematiquement : sans ca, re-selectionner le
  // meme fichier apres un echec ne declencherait aucun evenement.
  event.target.value = "";
  if (file) await app.savePhoto(file);
}

async function onPhotoRemove() {
  await app.removePhoto();
}

// --- Soumission ---
async function onSubmit() {
  await app.saveProfile({
    name: form.name,
    email: form.email,
    gender: form.gender,
    music_preference: form.music_preference,
    // Le backend vide aussi cette liste, mais l'envoyer deja vide evite que
    // la reponse contredise ce que l'utilisateur vient de voir a l'ecran.
    music_genres: showMusicGenres.value ? form.music_genres : [],
    smoking_preference: form.smoking_preference,
    // Champ vide = pas de voiture (null), sinon le nombre saisi.
    car_seats: form.car_seats === "" || form.car_seats === null ? null : Number(form.car_seats),
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

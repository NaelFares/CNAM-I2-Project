<template>
  <section class="single-card-center">
    <div class="page-card max-w-2xl">
      <div class="flex items-center justify-center gap-3">
        <div class="grid h-11 w-11 place-items-center rounded-xl border border-blue-200 bg-blue-50 text-blue-700">
          <UserRoundPlus class="h-5 w-5" />
        </div>
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Créer un compte</h1>
          <p class="text-sm font-medium text-slate-500">Quelques informations suffisent pour démarrer.</p>
        </div>
      </div>

      <form class="mt-8 grid gap-4 md:grid-cols-2" @submit.prevent="onSubmit">
        <div class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Nom complet</label>
          <input v-model="form.name" required class="input" />
        </div>

        <div class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
          <input v-model="form.email" type="email" required class="input" />
        </div>

        <div class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Sexe</label>
          <select v-model="form.gender" required class="input">
            <option value="" disabled>Sélectionnez…</option>
            <option v-for="option in GENDER_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Tabac</label>
          <select v-model="form.smoking_preference" class="input">
            <option v-for="option in SMOKING_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Musique</label>
          <select v-model="form.music_preference" class="input">
            <option v-for="option in MUSIC_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div v-if="showMusicGenres" class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">
            Styles de musique
            <span class="ml-1 font-normal text-slate-400">(facultatif, {{ MAX_MUSIC_GENRES }} max.)</span>
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="option in MUSIC_GENRE_OPTIONS"
              :key="option.value"
              type="button"
              :disabled="isGenreDisabled(option.value)"
              :class="[
                'rounded-full border px-3 py-1.5 text-sm font-semibold transition',
                form.music_genres.includes(option.value)
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                isGenreDisabled(option.value) ? 'cursor-not-allowed opacity-40' : '',
              ]"
              @click="toggleGenre(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="md:col-span-2">
          <p class="text-xs text-slate-500">
            La photo de profil se renseigne ensuite depuis votre profil.
          </p>
        </div>

        <div class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Mot de passe</label>
          <input v-model="form.password" type="password" required minlength="8" class="input" />
        </div>

        <div class="md:col-span-2">
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Confirmation de mot de passe</label>
          <input v-model="form.passwordConfirmation" type="password" required class="input" />
          <p v-if="passwordMismatch" class="mt-1 text-sm text-red-600">
            Les mots de passe ne correspondent pas.
          </p>
        </div>

        <div class="md:col-span-2 mt-2">
          <button class="btn-primary w-full" :disabled="auth.loading">
            <LoaderCircle v-if="auth.loading" class="h-4 w-4 animate-spin" />
            <UserRoundPlus v-else class="h-4 w-4" />
            Créer mon compte
          </button>
        </div>
      </form>

      <p class="mt-6 text-center text-sm text-slate-600">
        Déjà un compte ?
        <RouterLink to="/login" class="font-semibold text-blue-700 transition hover:text-blue-800">Se connecter
        </RouterLink>
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { LoaderCircle, UserRoundPlus } from "lucide-vue-next";

import { GENDER_OPTIONS } from "../lib/gender";
import {
  MAX_MUSIC_GENRES,
  MUSIC_GENRE_OPTIONS,
  MUSIC_OPTIONS,
  SMOKING_OPTIONS,
  wantsMusic,
} from "../lib/preferences";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

const form = reactive({
  name: "",
  email: auth.pendingEmail || "",
  gender: "",
  music_preference: "peu_importe",
  music_genres: [],
  smoking_preference: "peu_importe",
  password: "",
  passwordConfirmation: "",
});

const passwordMismatch = computed(
  () => form.passwordConfirmation.length > 0 && form.password !== form.passwordConfirmation
);

const showMusicGenres = computed(() => wantsMusic(form.music_preference));

function isGenreDisabled(value) {
  // Plafond atteint : on peut encore décocher, plus ajouter.
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

async function onSubmit() {
  if (form.password !== form.passwordConfirmation) return;
  // détachement de passwordConfirmation car il ne doit pas être stocké
  const { passwordConfirmation, ...payload } = form;
  // Cf. profil : pas de styles déclarés sans musique.
  if (!showMusicGenres.value) payload.music_genres = [];
  const ok = await auth.registerUser(payload);
  if (ok) {
    router.push("/");
  }
}
</script>

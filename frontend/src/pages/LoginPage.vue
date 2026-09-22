<template>
  <div class="min-h-screen" :class="{ 'mobile-preview-shell': display.mobilePreview }">
    <div class="flex justify-end px-4 pt-4 sm:px-6">
      <button
        type="button"
        class="btn-secondary header-icon-button"
        :aria-label="display.mobilePreview ? 'Revenir au mode ordinateur' : 'Afficher le mode téléphone'"
        :title="display.mobilePreview ? 'Mode ordinateur' : 'Mode téléphone'"
        @click="display.toggleDisplayMode"
      >
        <Monitor v-if="display.mobilePreview" class="h-4 w-4" />
        <Smartphone v-else class="h-4 w-4" />
      </button>
    </div>

    <section class="single-card-center px-4 py-4 sm:px-6 sm:py-8">
      <div class="page-card max-w-xl p-5 sm:p-7 md:p-9">
      <div class="flex flex-col items-center justify-center gap-3 text-center sm:flex-row sm:text-left">
        <div class="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-blue-200 bg-blue-50 text-blue-700">
          <LogIn class="h-5 w-5" />
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight sm:text-3xl">Connexion</h1>
          <p class="mt-1 text-sm font-medium leading-5 text-slate-500 sm:mt-0">
            Reprenez votre parcours de covoiturage campus.
          </p>
        </div>
      </div>

      <form class="mt-6 space-y-4 sm:mt-8 sm:space-y-5" @submit.prevent="onSubmit">
        <div>
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Adresse email</label>
          <input v-model="email" type="email" required class="input" placeholder="prenom.nom@etudiant.fr" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Mot de passe</label>
          <input v-model="password" type="password" required class="input" placeholder="Veuillez taper votre mot de passe" />
        </div>
        <button class="btn-primary w-full" :disabled="auth.loading">
          <LoaderCircle v-if="auth.loading" class="h-4 w-4 animate-spin" />
          <LogIn v-else class="h-4 w-4" />
          Se connecter
        </button>
      </form>

      <p class="mt-5 text-center text-sm leading-5 text-slate-600 sm:mt-6">
        Nouveau sur la plateforme ?
        <RouterLink to="/register" class="font-semibold text-blue-700 transition hover:text-blue-800">Créer un compte
        </RouterLink>
      </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { LoaderCircle, LogIn, Monitor, Smartphone } from "lucide-vue-next";

import { useAuthStore } from "../stores/auth";
import { useDisplayStore } from "../stores/display";

const auth = useAuthStore();
const display = useDisplayStore();
const router = useRouter();
const email = ref(auth.pendingEmail || "");
const password = ref("");

async function onSubmit() {
  const result = await auth.loginWithEmail(email.value, password.value);
  if (result.registerRequired) {
    router.push("/register");
    return;
  }
  if (auth.isLoggedIn) {
    router.push("/");
  }
}
</script>

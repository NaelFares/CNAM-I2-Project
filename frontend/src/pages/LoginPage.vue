<template>
  <section class="single-card-center">
    <div class="page-card max-w-xl">
      <div class="flex items-center justify-center gap-3">
        <div class="grid h-11 w-11 place-items-center rounded-xl border border-blue-200 bg-blue-50 text-blue-700">
          <LogIn class="h-5 w-5" />
        </div>
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Connexion</h1>
          <p class="text-sm font-medium text-slate-500">Reprenez votre parcours de covoiturage campus.</p>
        </div>
      </div>

      <form class="mt-8 space-y-5" @submit.prevent="onSubmit">
        <div>
          <label class="mb-1.5 block text-sm font-semibold text-slate-700">Adresse email</label>
          <input v-model="email" type="email" required class="input" placeholder="prenom.nom@etudiant.fr" />
        </div>
        <button class="btn-primary w-full" :disabled="auth.loading">
          <LoaderCircle v-if="auth.loading" class="h-4 w-4 animate-spin" />
          <LogIn v-else class="h-4 w-4" />
          Se connecter
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-slate-600">
        Nouveau sur la plateforme ?
        <RouterLink to="/register" class="font-semibold text-blue-700 transition hover:text-blue-800">Créer un compte</RouterLink>
      </p>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { LoaderCircle, LogIn } from "lucide-vue-next";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const email = ref(auth.pendingEmail || "");

async function onSubmit() {
  const result = await auth.loginWithEmail(email.value);
  if (result.registerRequired) {
    router.push("/register");
    return;
  }
  if (auth.isLoggedIn) {
    router.push("/");
  }
}
</script>

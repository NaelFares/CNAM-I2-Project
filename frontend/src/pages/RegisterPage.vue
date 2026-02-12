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
        <RouterLink to="/login" class="font-semibold text-blue-700 transition hover:text-blue-800">Se connecter</RouterLink>
      </p>
    </div>
  </section>
</template>

<script setup>
import { reactive } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { LoaderCircle, UserRoundPlus } from "lucide-vue-next";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

const form = reactive({
  name: "",
  email: auth.pendingEmail || "",
});

async function onSubmit() {
  const ok = await auth.registerUser(form);
  if (ok) {
    router.push("/");
  }
}
</script>

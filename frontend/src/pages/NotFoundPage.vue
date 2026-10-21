<template>
  <section class="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
    <span class="grid h-14 w-14 place-items-center rounded-full bg-slate-100 text-slate-500">
      <MapPinOff class="h-7 w-7" aria-hidden="true" />
    </span>
    <h1 class="page-title">Page introuvable</h1>
    <p class="page-subtitle">Cette adresse ne mène nulle part. Le lien est peut-être ancien ou mal recopié.</p>
    <RouterLink to="/" class="btn-primary">
      <House class="h-4 w-4" aria-hidden="true" />
      Retour à l'accueil
    </RouterLink>
  </section>
</template>

<script setup>
import { RouterLink } from "vue-router";
import { House, MapPinOff } from "lucide-vue-next";
</script>

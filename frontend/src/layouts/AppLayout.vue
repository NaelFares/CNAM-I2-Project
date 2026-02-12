<template>
  <div class="min-h-screen">
    <header class="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div class="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <div class="flex items-center gap-3">
          <Car class="h-7 w-7 text-blue-700" />
          <div>
            <p class="font-display text-base font-bold leading-tight text-slate-900">CovoitEtudiant</p>
            <p class="text-xs font-semibold text-slate-500">Mobilité campus</p>
          </div>
        </div>

        <nav class="hidden items-center gap-1 lg:flex">
          <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 transition"
            :class="$route.path === link.to ? 'bg-blue-100 text-blue-700' : 'hover:bg-slate-100 hover:text-slate-900'"
          >
            <component :is="link.icon" class="h-4 w-4" />
            {{ link.label }}
          </RouterLink>
        </nav>

        <button class="btn-secondary px-3 py-2" @click="handleLogout">
          <LogOut class="h-4 w-4" />
          Déconnexion
        </button>
      </div>

      <div class="mx-auto flex w-full max-w-6xl gap-2 overflow-x-auto px-4 pb-3 lg:hidden md:px-6">
        <RouterLink
          v-for="link in links"
          :key="`mobile-${link.to}`"
          :to="link.to"
          class="inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition"
          :class="$route.path === link.to ? 'bg-blue-100 text-blue-700' : 'bg-white text-slate-600'"
        >
          <component :is="link.icon" class="h-4 w-4" />
          {{ link.label }}
        </RouterLink>
      </div>
    </header>

    <main class="mx-auto w-full max-w-6xl px-4 py-7 md:px-6 md:py-9">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter, RouterLink, RouterView } from "vue-router";
import { Car, CalendarDays, LayoutDashboard, LogOut, Route, UserRound, UsersRound } from "lucide-vue-next";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const links = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { to: "/profile", label: "Profil", icon: UserRound },
  { to: "/schedule", label: "Planning", icon: CalendarDays },
  { to: "/rides", label: "Trajets", icon: Route },
  { to: "/matches", label: "Correspondances", icon: UsersRound },
];

async function handleLogout() {
  await auth.logout();
  router.push("/login");
}
</script>

<template>
  <div class="min-h-screen">
    <header class="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div class="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <div class="flex items-center gap-3">
          <img src="/logo.png" alt="Stud'Ride" class="h-16 w-16 rounded-full" />
          <div>
            <p class="font-display text-base font-bold leading-tight text-slate-900">Stud'Ride</p>
            <p class="text-xs font-semibold text-slate-500">Mobilité campus</p>
          </div>
        </div>

        <nav class="hidden items-center gap-1 lg:flex">
          <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 transition"
            :class="$route.path === link.to ? 'bg-primary-soft text-primary' : 'hover:bg-slate-100 hover:text-slate-900'"
          >
            <component :is="link.icon" class="h-4 w-4" />
            {{ link.label }}
          </RouterLink>
        </nav>

        <Button variant="secondary" class="px-3 py-2" @click="handleLogout">
          <LogOut class="h-4 w-4" />
          Déconnexion
        </Button>
      </div>

      <div class="mx-auto flex w-full max-w-6xl gap-2 overflow-x-auto px-4 pb-3 lg:hidden md:px-6">
        <RouterLink
          v-for="link in links"
          :key="`mobile-${link.to}`"
          :to="link.to"
          class="inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition"
          :class="$route.path === link.to ? 'bg-primary-soft text-primary' : 'bg-white text-slate-600'"
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
import { CalendarDays, LayoutDashboard, LogOut, UserRound, UsersRound } from "lucide-vue-next";

import { Button } from "../components/ui";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const links = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { to: "/profile", label: "Profil", icon: UserRound },
  { to: "/schedule", label: "Planning", icon: CalendarDays },
  { to: "/matches", label: "Covoiturage", icon: UsersRound },
];

async function handleLogout() {
  await auth.logout();
  router.push("/login");
}
</script>

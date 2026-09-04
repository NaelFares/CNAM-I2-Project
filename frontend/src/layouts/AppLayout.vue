<template>
  <div class="min-h-screen" :class="{ 'mobile-preview-shell': display.mobilePreview }">
    <header ref="headerRef" class="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
      <div
        class="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-3 py-2 lg:px-6 lg:py-3"
      >
        <div class="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="Stud'Ride"
            class="rounded-full"
            :class="display.mobilePreview ? 'h-10 w-10' : 'h-10 w-10 lg:h-16 lg:w-16'"
          />
          <div>
            <p class="font-display text-base font-bold leading-tight text-slate-900">Stud'Ride</p>
            <p v-if="!display.mobilePreview" class="hidden text-xs font-semibold text-slate-500 lg:block">Mobilité campus</p>
          </div>
        </div>

        <nav v-if="!display.mobilePreview" class="hidden items-center gap-1 lg:flex">
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

        <div class="flex items-center gap-2">
          <Button
            variant="secondary"
            class="header-icon-button"
            :aria-label="display.mobilePreview ? 'Revenir au mode ordinateur' : 'Afficher le mode téléphone'"
            :title="display.mobilePreview ? 'Mode ordinateur' : 'Mode téléphone'"
            @click="toggleDisplayMode"
          >
            <Monitor v-if="display.mobilePreview" class="h-4 w-4" />
            <Smartphone v-else class="h-4 w-4" />
          </Button>

          <Button v-if="!display.mobilePreview" variant="secondary" class="hidden px-3 py-2 lg:inline-flex" @click="handleLogout">
            <LogOut class="h-4 w-4" />
            Déconnexion
          </Button>

          <Button
            variant="secondary"
            class="header-icon-button"
            :class="{ 'lg:hidden': !display.mobilePreview }"
            :aria-expanded="mobileMenuOpen"
            aria-controls="mobile-navigation"
            :aria-label="mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'"
            :title="mobileMenuOpen ? 'Fermer le menu' : 'Menu'"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <X v-if="mobileMenuOpen" class="h-5 w-5" />
            <Menu v-else class="h-5 w-5" />
          </Button>
        </div>
      </div>

      <nav
        v-if="mobileMenuOpen"
        id="mobile-navigation"
        aria-label="Navigation mobile"
        class="mobile-navigation mx-auto w-full max-w-6xl border-t border-slate-200 px-3 py-3 lg:px-6"
      >
        <ul class="space-y-1">
          <li v-for="link in links" :key="`mobile-${link.to}`">
            <RouterLink
              :to="link.to"
              class="flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition"
              :class="$route.path === link.to ? 'bg-primary-soft text-primary' : 'text-slate-700 hover:bg-slate-100'"
              :aria-current="$route.path === link.to ? 'page' : undefined"
              @click="mobileMenuOpen = false"
            >
              <component :is="link.icon" class="h-5 w-5" />
              {{ link.label }}
            </RouterLink>
          </li>
        </ul>

        <div class="mt-3 border-t border-slate-200 pt-3">
          <Button variant="secondary" class="w-full justify-start" @click="handleLogout">
            <LogOut class="h-5 w-5" />
            Déconnexion
          </Button>
        </div>
      </nav>
    </header>

    <main class="mx-auto w-full max-w-6xl px-4 py-7 md:px-6 md:py-9">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter, RouterLink, RouterView } from "vue-router";
import { CalendarDays, LayoutDashboard, LogOut, Menu, Monitor, Smartphone, UserRound, UsersRound, X } from "lucide-vue-next";

import { Button } from "../components/ui";
import { useAuthStore } from "../stores/auth";
import { useDisplayStore } from "../stores/display";

const router = useRouter();
const auth = useAuthStore();
const display = useDisplayStore();
const mobileMenuOpen = ref(false);
const headerRef = ref(null);

const links = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { to: "/profile", label: "Profil", icon: UserRound },
  { to: "/schedule", label: "Planning", icon: CalendarDays },
  { to: "/matches", label: "Covoiturage", icon: UsersRound },
];

async function handleLogout() {
  mobileMenuOpen.value = false;
  await auth.logout();
  router.push("/login");
}

function toggleDisplayMode() {
  display.toggleDisplayMode();
  mobileMenuOpen.value = false;
}

function closeMenuFromOutside(event) {
  if (mobileMenuOpen.value && headerRef.value && !headerRef.value.contains(event.target)) {
    mobileMenuOpen.value = false;
  }
}

function closeMenuFromKeyboard(event) {
  if (event.key === "Escape") {
    mobileMenuOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener("pointerdown", closeMenuFromOutside);
  document.addEventListener("keydown", closeMenuFromKeyboard);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", closeMenuFromOutside);
  document.removeEventListener("keydown", closeMenuFromKeyboard);
});
</script>

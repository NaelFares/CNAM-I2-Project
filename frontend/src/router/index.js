import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MatchesPage from "../pages/MatchesPage.vue";
import ProfilePage from "../pages/ProfilePage.vue";
import RegisterPage from "../pages/RegisterPage.vue";
import RidesPage from "../pages/RidesPage.vue";
import SchedulePage from "../pages/SchedulePage.vue";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginPage },
    { path: "/register", component: RegisterPage },
    {
      path: "/",
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: "", component: DashboardPage },
        { path: "profile", component: ProfilePage },
        { path: "schedule", component: SchedulePage },
        { path: "rides", component: RidesPage },
        { path: "matches", component: MatchesPage },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.initialized) {
    await auth.restoreSession();
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return "/login";
  }
  if ((to.path === "/login" || to.path === "/register") && auth.isLoggedIn) {
    return "/";
  }
  return true;
});

export default router;

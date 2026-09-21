<template>
  <span
    :class="['inline-grid shrink-0 place-items-center overflow-hidden rounded-full font-semibold', sizeClasses, fallbackClasses]"
    :title="name || undefined"
  >
    <img
      v-if="photoUrl && !failed"
      :src="resolvedUrl"
      :alt="name ? `Photo de ${name}` : 'Photo de profil'"
      class="h-full w-full object-cover"
      @error="failed = true"
    />
    <!-- Repli sur les initiales : pas de photo, ou image illisible -->
    <span v-else aria-hidden="true">{{ initials }}</span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from "vue";

import { API_BASE_URL } from "../../api/api";

const props = defineProps({
  name: { type: String, default: "" },
  photoUrl: { type: String, default: "" },
  size: { type: String, default: "md" }, // 'sm' | 'md' | 'lg' | 'xl'
});

const failed = ref(false);

// Une nouvelle photo doit pouvoir s'afficher meme si la precedente avait
// echoue, sinon l'avatar reste bloque sur les initiales apres un televersement.
watch(() => props.photoUrl, () => (failed.value = false));

// Le backend renvoie un chemin absolu ("/media/..."), servi par l'API et non
// par le serveur du frontend : il faut le prefixer.
const resolvedUrl = computed(() =>
  props.photoUrl?.startsWith("/") ? `${API_BASE_URL}${props.photoUrl}` : props.photoUrl
);

const initials = computed(() => {
  const words = (props.name || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return "?";
  return words.slice(0, 2).map((word) => word[0].toUpperCase()).join("");
});

const sizeClasses = computed(() => {
  const map = {
    sm: "h-8 w-8 text-xs",
    md: "h-11 w-11 text-sm",
    lg: "h-16 w-16 text-lg",
    xl: "h-24 w-24 text-2xl",
  };
  return map[props.size] || map.md;
});

const fallbackClasses = computed(() =>
  props.photoUrl && !failed.value ? "bg-slate-100" : "bg-primary-soft text-primary"
);
</script>

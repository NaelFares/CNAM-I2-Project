<template>
  <div class="space-y-3">
    <p v-if="!ratings.length" class="text-sm text-slate-500">
      {{ emptyLabel }}
    </p>

    <article
      v-for="rating in ratings"
      :key="rating.id"
      class="flex gap-3 rounded-xl border border-slate-200 bg-white p-3"
    >
      <Avatar :name="rating.rater_name" :photo-url="rating.rater_photo_url" size="sm" />

      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span class="text-sm font-semibold text-slate-800">{{ rating.rater_name }}</span>
          <StarRating :value="rating.score" readonly size="sm" />
          <span class="ml-auto text-xs text-slate-400">{{ formatDate(rating.created_at) }}</span>
        </div>

        <!-- Le commentaire est facultatif : beaucoup de notes n'en ont pas -->
        <p v-if="rating.comment" class="mt-1 whitespace-pre-line break-words text-sm text-slate-600">
          {{ rating.comment }}
        </p>
        <p v-else class="mt-1 text-sm italic text-slate-400">Aucun commentaire.</p>
      </div>
    </article>
  </div>
</template>

<script setup>
import { Avatar, StarRating } from "./ui";

defineProps({
  ratings: { type: Array, default: () => [] },
  emptyLabel: { type: String, default: "Aucun avis pour le moment." },
});

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
}
</script>

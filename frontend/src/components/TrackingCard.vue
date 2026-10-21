<template>
  <Card padding="p-5" class="space-y-4">
    <div class="flex items-start gap-3">
      <Avatar :name="tracking.counterpart_name" :photo-url="tracking.counterpart_photo_url" size="md" />
      <div class="min-w-0 flex-1">
        <p class="card-title truncate">{{ tracking.counterpart_name }}</p>
        <div class="mt-1 flex flex-wrap items-center gap-2 text-[0.8125rem] text-slate-600">
          <RoleBadge :role="tracking.my_role" />
          <DirectionBadge :ride-type="tracking.ride_type" />
          <span>{{ formattedTime }}</span>
        </div>
      </div>
      <Badge :variant="statusVariant(tracking.status)">{{ statusLabel(tracking.status) }}</Badge>
    </div>

    <!-- Progression des quatre confirmations ; masquee dans l'historique,
         ou seul le resultat compte. -->
    <ol v-if="!compact" class="tracking-steps" aria-label="Étapes de la course">
      <li v-for="step in confirmationSteps(tracking)" :key="step.label" :class="{ 'is-done': step.at }">
        <span class="tracking-steps__dot">
          <Check v-if="step.at" class="h-3 w-3" aria-hidden="true" />
        </span>
        <span class="tracking-steps__label">{{ step.label }}</span>
        <span v-if="step.at" class="tracking-steps__time">{{ formatTime(step.at) }}</span>
      </li>
    </ol>

    <div v-if="!isFinished(tracking.status)" class="flex flex-wrap items-center gap-2">
      <Button v-if="tracking.next_step" :disabled="store.loading" @click="onConfirm">
        <Check class="h-4 w-4" />
        {{ stepLabel(tracking.next_step) }}
      </Button>
      <p v-else class="text-sm text-slate-500">{{ waitingMessage(tracking) }}</p>

      <!-- Annulation possible seulement avant toute confirmation : l'annulation
           supprime la reservation, et avec elle le suivi deja commence. -->
      <Button
        v-if="canCancel"
        variant="ghost"
        class="ml-auto"
        :disabled="store.loading || String(app.selectionLoadingRideId) === String(tracking.ride_id)"
        @click="onCancel"
      >
        <X class="h-4 w-4" />
        Annuler
      </Button>
    </div>

    <!-- Note deja donnee : definitive, donc affichee en lecture seule -->
    <div v-else-if="tracking.my_rating">
      <p class="flex items-center gap-2 text-sm text-slate-600">
        Votre note&nbsp;:
        <StarRating :value="tracking.my_rating" readonly />
      </p>
    </div>

    <!-- Formulaire de notation, une fois la course terminee -->
    <Button v-else-if="tracking.can_rate && !ratingOpen" variant="secondary" size="sm" @click="ratingOpen = true">
      <Star class="h-4 w-4" aria-hidden="true" />
      Noter la course
    </Button>
    <div v-else-if="tracking.can_rate" class="space-y-3 border-t border-slate-100 pt-3">
      <div>
        <p class="text-sm font-semibold text-slate-800">
          Comment s'est passée la course avec {{ tracking.counterpart_name }}&nbsp;?
        </p>
        <p class="text-xs text-slate-500">Votre note est définitive et ne pourra pas être modifiée.</p>
      </div>

      <StarRating v-model="score" />

      <textarea
        v-model="comment"
        rows="2"
        :maxlength="MAX_COMMENT_LENGTH"
        placeholder="Un commentaire ? (facultatif)"
        class="input resize-none text-sm"
      ></textarea>

      <!-- Confirmation explicite : la note etant irreversible, un clic seul
           ne doit pas suffire. -->
      <div v-if="confirming" class="flex flex-wrap items-center gap-2 rounded-xl bg-warning-soft p-3">
        <p class="text-sm text-warning">
          Confirmer {{ score }} étoile{{ score > 1 ? "s" : "" }}&nbsp;? C'est définitif.
        </p>
        <Button class="ml-auto" :disabled="store.loading" @click="onRate">
          <Check class="h-4 w-4" />
          Confirmer
        </Button>
        <Button variant="secondary" :disabled="store.loading" @click="confirming = false">
          Annuler
        </Button>
      </div>
      <Button v-else :disabled="!score || store.loading" @click="confirming = true">
        <Star class="h-4 w-4" />
        Envoyer ma note
      </Button>
    </div>
  </Card>
</template>

<script setup>
import { computed, ref } from "vue";
import { Check, Star, X } from "lucide-vue-next";

import { Avatar, Badge, Button, Card, DirectionBadge, RoleBadge, StarRating } from "./ui";
import { formatShortDateTime } from "../lib/format";
import {
  confirmationSteps,
  isFinished,
  statusLabel,
  statusVariant,
  stepLabel,
  waitingMessage,
} from "../lib/tracking";
import { useAppStore } from "../stores/app";
import { useTrackingStore } from "../stores/tracking";

const props = defineProps({
  tracking: { type: Object, required: true },
  // Historique : sans la progression detaillee.
  compact: { type: Boolean, default: false },
});

const store = useTrackingStore();
const app = useAppStore();

// Le passager peut renoncer a une course confirmee tant que personne n'a
// confirme la prise en charge (statut de suivi "pending").
const canCancel = computed(
  () => props.tracking.my_role === "passenger" && props.tracking.status === "pending"
);

async function onCancel() {
  const ok = await app.cancelRideSelection(props.tracking.ride_id);
  if (ok) await store.load();
}

// Limite alignee sur MAX_COMMENT_LENGTH cote backend.
const MAX_COMMENT_LENGTH = 500;

const score = ref(0);
const comment = ref("");
const confirming = ref(false);
// Formulaire replie par defaut : l'historique reste lisible.
const ratingOpen = ref(false);

async function onRate() {
  if (!score.value) return;
  const ok = await store.rate(props.tracking.id, score.value, comment.value);
  confirming.value = false;
  if (ok) {
    score.value = 0;
    comment.value = "";
  }
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

const formattedTime = computed(() => formatShortDateTime(props.tracking.ride_time));

async function onConfirm() {
  await store.confirm(props.tracking.id, props.tracking.next_step);
}
</script>

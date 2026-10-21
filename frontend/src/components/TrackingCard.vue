<template>
  <Card class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <Avatar :name="tracking.counterpart_name" :photo-url="tracking.counterpart_photo_url" size="md" />
        <div>
          <p class="font-semibold text-slate-900">{{ tracking.counterpart_name }}</p>
          <p class="text-xs text-slate-500">
            {{ roleLabel }} · {{ directionLabel }} · {{ formattedTime }}
          </p>
        </div>
      </div>
      <Badge :variant="statusVariant(tracking.status)">{{ statusLabel(tracking.status) }}</Badge>
    </div>

    <!-- Progression des quatre confirmations -->
    <ol class="space-y-1.5">
      <li
        v-for="step in confirmationSteps(tracking)"
        :key="step.label"
        class="flex items-center gap-2 text-sm"
      >
        <CircleCheck v-if="step.at" class="h-4 w-4 shrink-0 text-success" />
        <Circle v-else class="h-4 w-4 shrink-0 text-slate-300" />
        <span :class="step.at ? 'text-slate-700' : 'text-slate-400'">{{ step.label }}</span>
        <span v-if="step.at" class="ml-auto text-xs text-slate-400">{{ formatTime(step.at) }}</span>
      </li>
    </ol>

    <div v-if="!isFinished(tracking.status)" class="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
      <Button v-if="tracking.next_step" :disabled="store.loading" @click="onConfirm">
        <Check class="h-4 w-4" />
        {{ stepLabel(tracking.next_step) }}
      </Button>
      <p v-else class="text-sm text-slate-500">{{ waitingMessage(tracking) }}</p>

      <!-- Annulation possible seulement avant toute confirmation : l'annulation
           supprime la reservation, et avec elle le suivi deja commence. -->
      <Button
        v-if="canCancel"
        variant="secondary"
        class="ml-auto"
        :disabled="store.loading || String(app.selectionLoadingRideId) === String(tracking.ride_id)"
        @click="onCancel"
      >
        <X class="h-4 w-4" />
        Annuler
      </Button>
    </div>

    <!-- Note deja donnee : definitive, donc affichee en lecture seule -->
    <div v-else-if="tracking.my_rating" class="border-t border-slate-100 pt-3">
      <p class="flex items-center gap-2 text-sm text-slate-600">
        Votre note&nbsp;:
        <StarRating :value="tracking.my_rating" readonly />
      </p>
    </div>

    <!-- Formulaire de notation, une fois la course terminee -->
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
      <div v-if="confirming" class="flex flex-wrap items-center gap-2 rounded-xl bg-amber-50 p-3">
        <p class="text-sm text-amber-900">
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
import { Check, Circle, CircleCheck, Star, X } from "lucide-vue-next";

import { Avatar, Badge, Button, Card, StarRating } from "./ui";
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

async function onRate() {
  if (!score.value) return;
  const ok = await store.rate(props.tracking.id, score.value, comment.value);
  confirming.value = false;
  if (ok) {
    score.value = 0;
    comment.value = "";
  }
}

const roleLabel = computed(() =>
  props.tracking.my_role === "driver" ? "Votre passager" : "Votre conducteur"
);

const directionLabel = computed(() =>
  props.tracking.ride_type === "to_campus" ? "Vers le campus" : "Depuis le campus"
);

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

const formattedTime = computed(() => {
  const date = new Date(props.tracking.ride_time);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleString("fr-FR", {
        weekday: "short",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
});

async function onConfirm() {
  await store.confirm(props.tracking.id, props.tracking.next_step);
}
</script>

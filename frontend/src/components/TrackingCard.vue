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
    </div>
  </Card>
</template>

<script setup>
import { computed } from "vue";
import { Check, Circle, CircleCheck } from "lucide-vue-next";

import { Avatar, Badge, Button, Card } from "./ui";
import {
  confirmationSteps,
  isFinished,
  statusLabel,
  statusVariant,
  stepLabel,
  waitingMessage,
} from "../lib/tracking";
import { useTrackingStore } from "../stores/tracking";

const props = defineProps({
  tracking: { type: Object, required: true },
});

const store = useTrackingStore();

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

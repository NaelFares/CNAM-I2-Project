<template>
  <Teleport to="body">
    <div
      v-if="confirm.open"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/50 p-4"
      @click.self="confirm.answer(false)"
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
        class="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"
      >
        <div class="flex items-start gap-3">
          <TriangleAlert class="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
          <div>
            <h2 id="confirm-title" class="text-base font-bold text-slate-900">{{ confirm.title }}</h2>
            <p id="confirm-message" class="mt-1 text-sm text-slate-600">{{ confirm.message }}</p>
          </div>
        </div>
        <div class="mt-5 flex justify-end gap-2">
          <Button variant="secondary" @click="confirm.answer(false)">{{ confirm.cancelLabel }}</Button>
          <Button ref="confirmButton" @click="confirm.answer(true)">{{ confirm.confirmLabel }}</Button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { TriangleAlert } from "lucide-vue-next";

import { Button } from "./ui";
import { useConfirmStore } from "../stores/confirm";

const confirm = useConfirmStore();
const confirmButton = ref(null);

// Focus sur l'action principale a l'ouverture ; Echap annule.
watch(
  () => confirm.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    confirmButton.value?.$el?.focus();
  },
);

function onKeydown(event) {
  if (confirm.open && event.key === "Escape") confirm.answer(false);
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <Teleport to="body">
    <Transition name="side-panel">
      <div v-if="open" class="fixed inset-0 z-[70] flex justify-end bg-slate-900/40" @click.self="$emit('close')">
        <aside
          role="dialog"
          aria-modal="true"
          :aria-label="title"
          class="side-panel flex w-full flex-col bg-white shadow-2xl"
        >
          <header class="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div class="min-w-0">
              <h2 class="section-title">{{ title }}</h2>
              <slot name="subtitle" />
            </div>
            <button type="button" class="-mr-2 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Fermer" @click="$emit('close')">
              <X class="h-5 w-5" aria-hidden="true" />
            </button>
          </header>
          <div class="flex-1 overflow-y-auto px-5 py-4">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="border-t border-slate-100 px-5 py-4">
            <slot name="footer" />
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
// Panneau de detail : a droite sur ordinateur, en bas de l'ecran sur mobile.
import { onBeforeUnmount, onMounted } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
});

const emit = defineEmits(["close"]);

function onKeydown(event) {
  if (props.open && event.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<style scoped>
.side-panel {
  max-width: 28rem;
  height: 100%;
}

@media (max-width: 640px) {
  .side-panel {
    max-width: none;
    height: auto;
    max-height: 85dvh;
    margin-top: auto;
    border-radius: 1rem 1rem 0 0;
  }
}

.side-panel-enter-active,
.side-panel-leave-active {
  transition: opacity 180ms ease;
}

.side-panel-enter-active .side-panel,
.side-panel-leave-active .side-panel {
  transition: transform 200ms ease;
}

.side-panel-enter-from,
.side-panel-leave-to {
  opacity: 0;
}

.side-panel-enter-from .side-panel,
.side-panel-leave-to .side-panel {
  transform: translateX(24px);
}
</style>

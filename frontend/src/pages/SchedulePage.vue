<template>
  <section class="page-shell">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div class="page-header">
        <h1 class="page-title">Mon planning</h1>
        <p class="page-subtitle">Vos cours de la semaine : chaque jour de cours donne un aller et un retour.</p>
      </div>
      <Button v-if="!importOpen && !app.previewEvents.length" @click="importOpen = true">
        <Upload class="h-4 w-4" aria-hidden="true" />
        {{ app.events.length ? "Réimporter" : "Importer un planning" }}
      </Button>
    </header>

    <!-- Import en deux temps : apercu, puis confirmation -->
    <Card v-if="importOpen && !app.previewEvents.length" class="space-y-4">
      <SectionHeader title="Importer un planning" subtitle="Fichier ICS ou CSV exporté de votre ENT. Préférez un export récent.">
        <template #action>
          <Button variant="ghost" size="sm" aria-label="Fermer" @click="closeImport">
            <X class="h-4 w-4" aria-hidden="true" />
          </Button>
        </template>
      </SectionHeader>

      <input ref="fileInput" type="file" accept=".ics,.csv,text/calendar,text/csv" class="hidden" @change="onFileChange" />
      <button
        type="button"
        class="flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center transition hover:border-primary hover:bg-primary-soft"
        @click="fileInput?.click()"
      >
        <FileUp class="h-7 w-7 text-slate-400" aria-hidden="true" />
        <span class="text-sm font-semibold text-slate-800">{{ selectedFile ? selectedFile.name : "Choisir un fichier" }}</span>
        <span class="muted">ICS ou CSV</span>
      </button>

      <label v-if="isCsvSelected" class="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3">
        <input v-model="privacyMode" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300" />
        <span>
          <span class="flex items-center gap-1.5 text-sm font-medium text-slate-800">
            <ShieldCheck class="h-4 w-4 text-slate-500" aria-hidden="true" />
            Mode confidentialité
          </span>
          <span class="muted mt-0.5 block">
            Seuls les en-têtes du CSV sont envoyés au service d'IA. Aucune ligne n'est partagée, mais la détection peut être moins précise.
          </span>
        </span>
      </label>

      <div class="flex justify-end">
        <Button :disabled="!selectedFile || app.loading" @click="launchPreview">
          <Eye class="h-4 w-4" aria-hidden="true" />
          Prévisualiser
        </Button>
      </div>
    </Card>

    <Card v-if="app.previewEvents.length" class="space-y-4">
      <SectionHeader title="Vérifier l'import" :count="app.previewEvents.length" subtitle="Cours détectés dans le fichier. Rien n'est enregistré avant confirmation." />
      <ShowMore :items="app.previewEvents" :limit="8" list-class="divide-y divide-slate-100 rounded-xl border border-slate-200">
        <template #default="{ item: event }">
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2 text-sm">
            <span class="min-w-0 flex-1 font-medium text-slate-900">{{ event.title }}</span>
            <span class="text-slate-600">{{ formatDay(event.start_time) }}</span>
            <span class="tabular-nums text-slate-600">{{ formatTime(event.start_time) }} – {{ formatTime(event.end_time) }}</span>
          </div>
        </template>
      </ShowMore>
      <div class="flex flex-wrap justify-end gap-2">
        <Button variant="secondary" @click="cancelImport">Annuler</Button>
        <Button :disabled="app.loading" @click="confirmImport">
          <Check class="h-4 w-4" aria-hidden="true" />
          Confirmer l'import
        </Button>
      </div>
    </Card>

    <Card v-if="app.events.length">
      <WeekCalendar :monday="week" :items="calendarItems" :split="false" empty-label="Pas de cours" @navigate="moveWeek">
        <template #item="{ item }">
          <div class="calendar-chip calendar-chip--out">
            <span class="tabular-nums text-xs font-semibold text-slate-500">{{ item.start }} – {{ item.end }}</span>
            <span class="line-clamp-2 font-medium text-slate-900">{{ item.title }}</span>
            <span v-if="item.location && item.location !== schoolOf(item.title)" class="truncate text-xs text-slate-500">{{ item.location }}</span>
          </div>
        </template>
      </WeekCalendar>
    </Card>

    <EmptyState
      v-else-if="!importOpen && !app.previewEvents.length"
      :icon="CalendarDays"
      title="Aucun cours pour l'instant"
      text="Importez votre emploi du temps : vos trajets de cours seront prêts à chercher ou à proposer."
    >
      <Button size="sm" @click="importOpen = true">
        <Upload class="h-4 w-4" aria-hidden="true" />
        Importer un planning
      </Button>
    </EmptyState>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { CalendarDays, Check, Eye, FileUp, ShieldCheck, Upload, X } from "lucide-vue-next";

import WeekCalendar from "../components/WeekCalendar.vue";
import { Button, Card, EmptyState, SectionHeader, ShowMore } from "../components/ui";
import { formatDay, formatTime } from "../lib/format";
import { localDateIso, mondayIso, nextUpcomingEvent, shiftWeek } from "../lib/week";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const fileInput = ref(null);
const selectedFile = ref(null);
const privacyMode = ref(false);
const importOpen = ref(false);
const week = ref(mondayIso(localDateIso()));

const isCsvSelected = computed(() => selectedFile.value?.name.toLowerCase().endsWith(".csv") ?? false);

const calendarItems = computed(() =>
  app.events.map((event, index) => ({
    key: `${event.start_time}-${index}`,
    date: String(event.start_time),
    outbound: true,
    title: event.title,
    location: event.location,
    start: formatTime(event.start_time),
    end: formatTime(event.end_time),
  })),
);

// "Cours a ENSEEIHT (N7)" a deja son lieu dans le titre : inutile de le repeter.
function schoolOf(title) {
  return String(title || "").replace(/^Cours à\s+/, "");
}

function moveWeek(offset) {
  week.value = offset === 0 ? mondayIso(localDateIso()) : shiftWeek(week.value, offset);
}

// Le calendrier s'ouvre sur la semaine du prochain cours (sinon du premier).
watch(
  () => app.events,
  (events) => {
    if (!events.length) return;
    const next = nextUpcomingEvent(events) || [...events].sort((a, b) => String(a.start_time).localeCompare(String(b.start_time)))[0];
    week.value = mondayIso(String(next.start_time).slice(0, 10));
  },
  { immediate: true },
);

onMounted(() => app.loadScheduleEvents());

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] ?? null;
  if (!isCsvSelected.value) privacyMode.value = false;
}

function closeImport() {
  importOpen.value = false;
  selectedFile.value = null;
}

async function launchPreview() {
  if (selectedFile.value) await app.previewSchedule(selectedFile.value, privacyMode.value);
}

async function confirmImport() {
  await app.confirmSchedule();
  closeImport();
}

async function cancelImport() {
  await app.cancelSchedulePreview();
  closeImport();
}
</script>

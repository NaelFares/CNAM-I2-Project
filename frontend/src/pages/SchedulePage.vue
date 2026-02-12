<template>
  <section class="page-shell">
    <header class="page-header">
      <h1 class="page-title">Mon emploi du temps</h1>
      <p class="page-subtitle">Importez, verifiez la previsualisation, puis confirmez l'import.</p>
    </header>

    <div class="advice-banner">
      Conseil: preferez un export ICS/CSV recent pour eviter les ecarts de planning.
    </div>

    <div class="card p-6">
      <div v-if="!app.previewEvents.length" class="mx-auto max-w-2xl space-y-4">
        <label class="mb-1 block text-sm font-semibold text-slate-700">Fichier planning</label>
        <input ref="fileInput" type="file" accept=".ics,.csv,text/calendar,text/csv" class="hidden" @change="onFileChange" />
        <div class="rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 p-5">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-700">
                {{ selectedFile ? selectedFile.name : "Aucun fichier selectionne" }}
              </p>
              <p class="text-xs text-slate-500">Formats acceptes: ICS, CSV.</p>
            </div>
            <button type="button" class="btn-secondary" @click="openFilePicker">
              <Upload class="h-4 w-4" />
              Choisir un fichier
            </button>
          </div>
        </div>
        <div class="flex justify-end">
          <button class="btn-primary" :disabled="!selectedFile || app.loading" @click="launchPreview">
            <Upload class="h-4 w-4" />
            Previsualiser
          </button>
        </div>
      </div>

      <div v-else class="space-y-4">
        <h2 class="text-xl font-bold text-slate-900">{{ app.previewEvents.length }} cours detectes (previsualisation)</h2>

        <div class="overflow-hidden rounded-xl border border-slate-200">
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-slate-900 text-slate-50">
                <tr>
                  <th class="px-3 py-2 text-left font-semibold">Titre</th>
                  <th class="px-3 py-2 text-left font-semibold">Debut</th>
                  <th class="px-3 py-2 text-left font-semibold">Fin</th>
                  <th class="px-3 py-2 text-left font-semibold">Lieu</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in app.previewEvents" :key="`${event.title}-${event.start_time}`" class="border-t border-slate-200 bg-white">
                  <td class="px-3 py-2 font-medium text-slate-800">{{ event.title }}</td>
                  <td class="px-3 py-2 text-slate-600">{{ formatDateTime(event.start_time) }}</td>
                  <td class="px-3 py-2 text-slate-600">{{ formatDateTime(event.end_time) }}</td>
                  <td class="px-3 py-2 text-slate-600">{{ event.location || "-" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="flex flex-wrap justify-end gap-3">
          <button class="btn-secondary" @click="cancel">
            <X class="h-4 w-4" />
            Annuler
          </button>
          <button class="btn-primary" :disabled="app.loading" @click="confirm">
            <Check class="h-4 w-4" />
            Confirmer l'import
          </button>
        </div>
      </div>
    </div>

    <div v-if="app.events.length" class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="flex items-center gap-2 text-xl font-bold text-slate-900">
          <CalendarDays class="h-5 w-5 text-blue-700" />
          Calendrier hebdomadaire
        </h2>
        <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">{{ app.events.length }} cours</span>
      </div>

      <div class="card p-4">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="text-sm font-semibold text-slate-700">{{ currentWeekLabel }}</div>
          <div class="flex items-center gap-2">
            <button class="btn-secondary px-3 py-2" @click="goPreviousWeek">
              <ChevronLeft class="h-4 w-4" />
              Semaine precedente
            </button>
            <button class="btn-secondary px-3 py-2" @click="goCurrentWeek">Cette semaine</button>
            <button class="btn-secondary px-3 py-2" @click="goNextWeek">
              Semaine suivante
              <ChevronRight class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
          <article v-for="day in weekDays" :key="day.key" class="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
            <header class="mb-2 border-b border-slate-200 pb-2">
              <p class="text-sm font-bold text-slate-800">{{ day.label }}</p>
              <p class="text-xs font-medium text-slate-500">{{ day.dateLabel }}</p>
            </header>

            <div v-if="day.events.length" class="space-y-2">
              <div v-for="event in day.events" :key="`${event.title}-${event.start_time}`" class="rounded-lg border border-slate-200 bg-white p-2">
                <p class="text-sm font-semibold text-slate-900">{{ event.title }}</p>
                <p class="text-xs font-medium text-slate-600">{{ formatTime(event.start_time) }} - {{ formatTime(event.end_time) }}</p>
                <p class="mt-1 line-clamp-2 text-xs text-slate-500">{{ event.location || "Lieu non renseigne" }}</p>
              </div>
            </div>
            <p v-else class="text-xs font-medium text-slate-400">Aucun cours</p>
          </article>
        </div>
      </div>
    </div>

    <div v-else class="card p-6 text-sm text-slate-600">
      Aucun cours enregistre pour le moment. Importez un fichier puis confirmez l'import pour voir votre emploi du temps ici.
    </div>
  </section>
</template>

<script setup>
import dayjs from "dayjs";
import { computed, onMounted, ref, watch } from "vue";
import { CalendarDays, Check, ChevronLeft, ChevronRight, Upload, X } from "lucide-vue-next";

import { cancelPreview } from "../api/endpoints";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const selectedFile = ref(null);
const fileInput = ref(null);
const weekStart = ref(getWeekStart(dayjs()));

const weekDays = computed(() => {
  const days = [];
  for (let i = 0; i < 7; i += 1) {
    const date = weekStart.value.add(i, "day");
    const start = date.startOf("day");
    const end = date.endOf("day");
    const events = app.events
      .filter((event) => {
        const dt = dayjs(event.start_time);
        return !dt.isBefore(start) && !dt.isAfter(end);
      })
      .sort((a, b) => dayjs(a.start_time).valueOf() - dayjs(b.start_time).valueOf());

    days.push({
      key: date.format("YYYY-MM-DD"),
      label: formatWeekday(date),
      dateLabel: date.format("DD/MM"),
      events,
    });
  }
  return days;
});

const currentWeekLabel = computed(() => {
  const start = weekStart.value;
  const end = weekStart.value.add(6, "day");
  return `Semaine du ${start.format("DD/MM/YYYY")} au ${end.format("DD/MM/YYYY")}`;
});

onMounted(async () => {
  await app.loadScheduleEvents();
});

watch(
  () => app.events,
  (events) => {
    if (!events.length) {
      weekStart.value = getWeekStart(dayjs());
      return;
    }
    const sorted = [...events].sort((a, b) => dayjs(a.start_time).valueOf() - dayjs(b.start_time).valueOf());
    weekStart.value = getWeekStart(dayjs(sorted[0].start_time));
  },
  { immediate: true, deep: true }
);

function getWeekStart(value) {
  const d = dayjs(value);
  const day = d.day();
  const offset = day === 0 ? 6 : day - 1;
  return d.subtract(offset, "day").startOf("day");
}

function formatWeekday(date) {
  const labels = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
  const day = date.day();
  return labels[day === 0 ? 6 : day - 1];
}

function goPreviousWeek() {
  weekStart.value = weekStart.value.subtract(7, "day");
}

function goNextWeek() {
  weekStart.value = weekStart.value.add(7, "day");
}

function goCurrentWeek() {
  weekStart.value = getWeekStart(dayjs());
}

function openFilePicker() {
  fileInput.value?.click();
}

function onFileChange(event) {
  const input = event.target;
  selectedFile.value = input.files?.[0] ?? null;
}

async function launchPreview() {
  if (!selectedFile.value) return;
  await app.previewSchedule(selectedFile.value);
}

async function confirm() {
  await app.confirmSchedule();
}

async function cancel() {
  await cancelPreview();
  app.previewEvents = [];
}

function formatDateTime(value) {
  return dayjs(value).format("DD/MM/YYYY HH:mm");
}

function formatTime(value) {
  return dayjs(value).format("HH:mm");
}
</script>

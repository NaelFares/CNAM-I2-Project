<template>
  <section class="week-calendar" :aria-label="`Semaine du ${periodLabel}`">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm font-semibold text-slate-900">{{ periodLabel }}</p>
      <div v-if="navigable" class="flex items-center gap-1">
        <button type="button" class="week-calendar__nav" aria-label="Semaine précédente" @click="$emit('navigate', -1)">
          <ChevronLeft class="h-4 w-4" aria-hidden="true" />
        </button>
        <button type="button" class="btn-ghost btn-sm" @click="$emit('navigate', 0)">Aujourd'hui</button>
        <button type="button" class="week-calendar__nav" aria-label="Semaine suivante" @click="$emit('navigate', 1)">
          <ChevronRight class="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div class="week-calendar__grid" :style="{ '--days': days.length }">
      <div
        v-for="day in days"
        :key="day.iso"
        class="week-calendar__day"
        :class="{ 'is-today': day.iso === todayIso, 'is-active': day.iso === activeDay, 'is-empty': !day.items.length }"
      >
        <component
          :is="selectableDays ? 'button' : 'div'"
          :type="selectableDays ? 'button' : undefined"
          class="week-calendar__day-head"
          :aria-pressed="selectableDays ? day.iso === activeDay : undefined"
          @click="selectableDays && $emit('select-day', day.iso)"
        >
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ day.weekday }}</span>
          <span class="week-calendar__date">{{ day.date }}</span>
          <span v-if="$slots['day-badge']" class="week-calendar__day-badge"><slot name="day-badge" :day="day" /></span>
        </component>

        <div v-if="day.items.length" class="week-calendar__slots">
          <div v-for="part in parts(day)" :key="part.key" class="week-calendar__part">
            <span v-if="split" class="week-calendar__part-label" :class="part.outbound ? 'text-outbound' : 'text-return'">
              <component :is="part.outbound ? School : House" class="h-3.5 w-3.5" aria-hidden="true" />
              {{ part.outbound ? "Aller" : "Retour" }}
            </span>
            <slot v-for="item in part.items" :key="item.key" name="item" :item="item" :day="day" />
          </div>
        </div>
        <p v-else class="week-calendar__none">{{ emptyLabel }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
// Calendrier partagé entre les pages ; le parent remplit les cases (slot item).
// Aller / retour séparés, sauf pour les cours.
import { computed } from "vue";
import { ChevronLeft, ChevronRight, House, School } from "lucide-vue-next";

import { calendarWeekDays, localDateIso } from "../lib/week";

const props = defineProps({
  monday: { type: String, required: true },
  // [{ key, date: ISO datetime, outbound: bool, ... }]
  items: { type: Array, default: () => [] },
  navigable: { type: Boolean, default: true },
  selectableDays: { type: Boolean, default: false },
  activeDay: { type: String, default: "" },
  emptyLabel: { type: String, default: "—" },
  // false : pas de separation Aller / Retour (cours du planning).
  split: { type: Boolean, default: true },
});

defineEmits(["navigate", "select-day"]);

const todayIso = localDateIso();

const days = computed(() => {
  const week = calendarWeekDays(props.monday).map((day) => {
    const date = new Date(`${day.iso}T12:00:00`);
    return {
      iso: day.iso,
      weekday: date.toLocaleDateString("fr-FR", { weekday: "short" }).replace(".", ""),
      date: date.getDate(),
      items: props.items
        .filter((item) => String(item.date).slice(0, 10) === day.iso)
        .sort((a, b) => String(a.date).localeCompare(String(b.date))),
    };
  });
  // Le week-end n'apparait que s'il a des trajets.
  return week.filter((day, index) => index < 5 || day.items.length);
});

function parts(day) {
  if (!props.split) return [{ key: "all", outbound: true, items: day.items }];
  return [true, false]
    .map((outbound) => ({ key: outbound ? "out" : "back", outbound, items: day.items.filter((item) => item.outbound === outbound) }))
    .filter((part) => part.items.length);
}

const periodLabel = computed(() => {
  const week = calendarWeekDays(props.monday);
  if (!week.length) return "";
  const format = (iso, withMonth) =>
    new Date(`${iso}T12:00:00`).toLocaleDateString("fr-FR", withMonth ? { day: "numeric", month: "long" } : { day: "numeric" });
  const first = week[0].iso;
  const last = week[4].iso;
  const sameMonth = first.slice(0, 7) === last.slice(0, 7);
  return `${format(first, !sameMonth)} – ${format(last, true)}`;
});
</script>

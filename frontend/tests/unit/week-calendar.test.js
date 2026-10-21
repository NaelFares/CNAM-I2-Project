import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import WeekCalendar from "../../src/components/WeekCalendar.vue";
import { useTrackingStore } from "../../src/stores/tracking";

const items = [
  { key: "a", date: "2026-10-26T08:00", outbound: true, label: "Aller lundi" },
  { key: "b", date: "2026-10-26T17:00", outbound: false, label: "Retour lundi" },
  { key: "c", date: "2026-10-28T10:00", outbound: true, label: "Aller mercredi" },
];

function mountCalendar(props = {}) {
  return mount(WeekCalendar, {
    props: { monday: "2026-10-26", items, ...props },
    slots: { item: '<template #item="{ item }"><span class="chip">{{ item.label }}</span></template>' },
  });
}

describe("WeekCalendar", () => {
  it("affiche les cinq jours de cours, sans le week-end vide", () => {
    expect(mountCalendar().findAll(".week-calendar__day")).toHaveLength(5);
  });

  it("separe l'aller et le retour de chaque jour", () => {
    const monday = mountCalendar().findAll(".week-calendar__day")[0];
    const labels = monday.findAll(".week-calendar__part-label").map((label) => label.text());
    expect(labels).toEqual(["Aller", "Retour"]);
    expect(monday.findAll(".chip").map((chip) => chip.text())).toEqual(["Aller lundi", "Retour lundi"]);
  });

  it("ajoute le samedi seulement s'il a des trajets", () => {
    const wrapper = mountCalendar({ items: [...items, { key: "d", date: "2026-10-31T09:00", outbound: true, label: "Samedi" }] });
    expect(wrapper.findAll(".week-calendar__day")).toHaveLength(6);
  });

  it("emet la navigation de semaine", async () => {
    const wrapper = mountCalendar();
    await wrapper.get('[aria-label="Semaine suivante"]').trigger("click");
    expect(wrapper.emitted("navigate")?.[0]).toEqual([1]);
  });
});

describe("Mes courses : en cours, a venir, historique", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("ne met en cours que les courses du jour ou deja commencees", () => {
    const store = useTrackingStore();
    const today = new Date();
    const later = new Date(today.getTime() + 3 * 24 * 3600 * 1000);
    store.trackings = [
      { id: 1, status: "pending", ride_time: later.toISOString() },
      { id: 2, status: "pending", ride_time: today.toISOString() },
      { id: 3, status: "on_board", ride_time: later.toISOString() },
      { id: 4, status: "completed", ride_time: today.toISOString() },
    ];
    expect(store.active.map((t) => t.id).sort()).toEqual([2, 3]);
    expect(store.upcoming.map((t) => t.id)).toEqual([1]);
    expect(store.finished.map((t) => t.id)).toEqual([4]);
  });
});

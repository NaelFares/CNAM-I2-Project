import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import RankedMatchesExplorer from "../../src/components/RankedMatchesExplorer.vue";

const matches = [
  {
    ride_id: 101,
    driver_id: 1,
    passenger_id: 7,
    driver_name: "Alice Martin",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:15",
    score: 96,
    extra_time_min: 3.2,
    distance_km: 4.1,
    route_geometry: [[48.8, 2.2], [48.9, 2.3]],
    car_seats: 4,
    available_seats: 2,
  },
  {
    ride_id: 102,
    driver_id: 2,
    passenger_id: 7,
    driver_name: "Liam Robert",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:20",
    score: 96,
    extra_time_min: 4.4,
    distance_km: 5.3,
    route_geometry: [[48.7, 2.1], [48.9, 2.3]],
    car_seats: 3,
    available_seats: 1,
  },
  {
    ride_id: 103,
    driver_id: 3,
    passenger_id: 7,
    driver_name: "Sam Durand",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:05",
    score: 89,
    extra_time_min: 2.1,
    distance_km: 2.8,
    route_geometry: [[48.75, 2.15], [48.9, 2.3]],
    car_seats: 4,
    available_seats: 4,
  },
];

describe("RankedMatchesExplorer", () => {
  it("regroupe les ex aequo en or et synchronise la sélection avec la carte", async () => {
    const wrapper = mount(RankedMatchesExplorer, {
      props: { matches },
      global: {
        stubs: {
          RouteMap: {
            props: ["routes", "selectedRouteIndex"],
            emits: ["select-route"],
            template: '<button data-test="map-route" @click="$emit(\'select-route\', 2)">Carte</button>',
          },
        },
      },
    });

    expect(wrapper.find(".matches-explorer__gold-group small").text()).toContain("2 trajets à 96 %");
    expect(wrapper.findAll(".ranked-match-card")).toHaveLength(3);
    expect(wrapper.findAll(".ranked-match-card")[0].attributes("aria-current")).toBe("true");

    await wrapper.get('[data-test="map-route"]').trigger("click");

    expect(wrapper.findAll(".ranked-match-card")[2].attributes("aria-current")).toBe("true");
  });

  it("emet le trajet conducteur quand le passager le selectionne", async () => {
    const wrapper = mount(RankedMatchesExplorer, {
      props: { matches },
      global: { stubs: { RouteMap: true } },
    });

    await wrapper.findAll(".ranked-match-card__choose")[0].trigger("click");

    expect(wrapper.emitted("choose-ride")?.[0]?.[0].ride_id).toBe(101);
  });

  it("n'affiche qu'une fois un meme trajet conducteur", () => {
    const duplicate = {
      ...matches[0],
      score: 91,
      extra_time_min: 5.5,
    };
    const wrapper = mount(RankedMatchesExplorer, {
      props: { matches: [...matches, duplicate] },
      global: { stubs: { RouteMap: true } },
    });

    expect(wrapper.findAll(".ranked-match-card")).toHaveLength(3);
    expect(wrapper.text()).not.toContain("91 %");
  });
});

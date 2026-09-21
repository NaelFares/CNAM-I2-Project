import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import RankedMatchesExplorer from "../../src/components/RankedMatchesExplorer.vue";

const matches = [
  {
    driver_id: 1,
    passenger_id: 7,
    driver_name: "Alice Martin",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:15",
    score: 96,
    extra_time_min: 3.2,
    distance_km: 4.1,
    route_geometry: [[48.8, 2.2], [48.9, 2.3]],
  },
  {
    driver_id: 2,
    passenger_id: 7,
    driver_name: "Liam Robert",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:20",
    score: 96,
    extra_time_min: 4.4,
    distance_km: 5.3,
    route_geometry: [[48.7, 2.1], [48.9, 2.3]],
  },
  {
    driver_id: 3,
    passenger_id: 7,
    driver_name: "Sam Durand",
    passenger_name: "Nora Petit",
    ride_time: "2026-09-07 08:05",
    score: 89,
    extra_time_min: 2.1,
    distance_km: 2.8,
    route_geometry: [[48.75, 2.15], [48.9, 2.3]],
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
    expect(wrapper.findAll(".ranked-match-card")[0].attributes("aria-pressed")).toBe("true");

    await wrapper.get('[data-test="map-route"]').trigger("click");

    expect(wrapper.findAll(".ranked-match-card")[2].attributes("aria-pressed")).toBe("true");
  });
});

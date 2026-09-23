import { describe, expect, it } from "vitest";

import { calendarWeekDays, matchesForDay, mondayIso, ridesForWeek, schoolWeekDays, shiftWeek } from "../../src/lib/week";

describe("recherche hebdomadaire", () => {
  it("sélectionne la semaine de cours contenant la date choisie", () => {
    const monday = mondayIso("2026-09-30");
    expect(monday).toBe("2026-09-28");
    expect(schoolWeekDays(monday).map((day) => day.iso)).toEqual([
      "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02",
    ]);
  });

  it("n'affiche que les trajets du jour actif", () => {
    const matches = [
      { ride_time: "2026-09-28 08:00" },
      { ride_time: "2026-09-29 12:00" },
    ];
    expect(matchesForDay(matches, "2026-09-29")).toEqual([matches[1]]);
    expect(matchesForDay(matches, "2026-09-30")).toEqual([]);
  });

  it("permet au conducteur de passer d'une semaine à l'autre", () => {
    expect(shiftWeek("2026-09-28", 1)).toBe("2026-10-05");
    expect(shiftWeek("2026-09-28", -1)).toBe("2026-09-21");
    expect(calendarWeekDays("2026-09-28").at(-1).iso).toBe("2026-10-04");

    const rides = [
      { ride_time: "2026-10-05T08:00:00" },
      { ride_time: "2026-10-04T12:00:00" },
      { ride_time: "2026-09-28T08:00:00" },
    ];
    expect(ridesForWeek(rides, "2026-09-28")).toEqual([rides[2], rides[1]]);
    expect(ridesForWeek(rides, "2026-10-05")).toEqual([rides[0]]);
  });
});

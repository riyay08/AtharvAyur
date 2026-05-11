import { describe, expect, it } from "vitest";

import {
  checkInIsToday,
  extractDominantDosha,
  todayPlanTaskCounts,
} from "./wellnessDashboard.js";

describe("wellnessDashboard", () => {
  it("extracts dominant dosha from nested conditions", () => {
    expect(
      extractDominantDosha({
        conditions: { prakriti_quiz: { dominant_dosha: "pitta" } },
      })
    ).toBe("pitta");
    expect(extractDominantDosha(null)).toBe(null);
    expect(extractDominantDosha({ conditions: {} })).toBe(null);
  });

  it("detects check-in logged today", () => {
    const ymd = "2099-01-15";
    const now = new Date(2099, 0, 15);
    expect(checkInIsToday({ check_in_date: ymd }, now)).toBe(true);
    expect(checkInIsToday({ check_in_date: "2099-01-14" }, now)).toBe(false);
  });

  it("counts today plan tasks from envelope", () => {
    const tasks = {
      days: [
        {
          date: "2099-01-15",
          pillars: {
            Mind: [{ completed: true }, { completed: false }],
            Fuel: [{ completed: false }],
          },
        },
      ],
    };
    const now = new Date(2099, 0, 15);
    expect(todayPlanTaskCounts(tasks, "2099-01-11", now)).toEqual({ done: 1, total: 3 });
  });
});

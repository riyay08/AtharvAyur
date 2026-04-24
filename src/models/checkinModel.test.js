import { describe, expect, it } from "vitest";

import {
  DEFAULT_FORM,
  dayLabel,
  formFromRecord,
  localYmd,
  normalizeYmd,
} from "./checkinModel.js";

describe("localYmd", () => {
  it("formats local date components zero-padded", () => {
    expect(localYmd(new Date(2026, 3, 5))).toBe("2026-04-05");
  });
});

describe("normalizeYmd", () => {
  it("trims ISO timestamps to the date portion", () => {
    expect(normalizeYmd("2026-04-22T07:08:09Z")).toBe("2026-04-22");
    expect(normalizeYmd("2026-04-22")).toBe("2026-04-22");
    expect(normalizeYmd(null)).toBe("");
    expect(normalizeYmd(undefined)).toBe("");
  });
});

describe("formFromRecord", () => {
  it("returns defaults for null/undefined", () => {
    expect(formFromRecord(null)).toEqual(DEFAULT_FORM);
    expect(formFromRecord(undefined)).toEqual(DEFAULT_FORM);
  });

  it("filters invalid enum values to the default", () => {
    const form = formFromRecord({
      sleep_quality: "bogus",
      digestion: "bogus",
      energy_state: "bogus",
      movement: "bogus",
      water_glasses: -3,
    });
    expect(form).toEqual(DEFAULT_FORM);
  });

  it("accepts valid values verbatim", () => {
    const form = formFromRecord({
      sleep_quality: "restless",
      digestion: "bloated",
      energy_state: "wired",
      movement: "sweat",
      water_glasses: 4,
    });
    expect(form).toEqual({
      sleepQuality: "restless",
      digestion: "bloated",
      energyState: "wired",
      movement: "sweat",
      water: 4,
    });
  });
});

describe("dayLabel", () => {
  it("returns short weekday and day number", () => {
    const { dayNum } = dayLabel("2026-04-22");
    expect(dayNum).toBe(22);
  });
});

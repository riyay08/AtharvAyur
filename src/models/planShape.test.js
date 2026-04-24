import { describe, expect, it } from "vitest";

import {
  allDone,
  countDone,
  dayIndexForToday,
  firstOpenTask,
  isEnvelope,
  localYmd,
  pillarTasks,
  resolveTodayDay,
} from "./planShape.js";

describe("localYmd", () => {
  it("formats a Date to YYYY-MM-DD in local time", () => {
    expect(localYmd(new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(localYmd(new Date(2026, 11, 31))).toBe("2026-12-31");
  });
});

describe("isEnvelope", () => {
  it("is true only for objects with a days array", () => {
    expect(isEnvelope({ days: [] })).toBe(true);
    expect(isEnvelope({ days: [{ date: "2026-01-01", pillars: {} }] })).toBe(true);
    expect(isEnvelope([])).toBe(false);
    expect(isEnvelope(null)).toBe(false);
    expect(isEnvelope(undefined)).toBe(false);
    expect(isEnvelope({})).toBe(false);
  });
});

describe("dayIndexForToday", () => {
  it("returns 0..6 when today is inside the week", () => {
    const now = new Date(2026, 3, 22);
    expect(dayIndexForToday("2026-04-20", now)).toBe(2);
    expect(dayIndexForToday("2026-04-22", now)).toBe(0);
    expect(dayIndexForToday("2026-04-16", now)).toBe(6);
  });

  it("returns null outside the week or for invalid inputs", () => {
    const now = new Date(2026, 3, 22);
    expect(dayIndexForToday("2026-04-15", now)).toBeNull();
    expect(dayIndexForToday("2026-04-23", now)).toBeNull();
    expect(dayIndexForToday("", now)).toBeNull();
    expect(dayIndexForToday("not-a-date", now)).toBeNull();
  });
});

describe("resolveTodayDay", () => {
  it("prefers a matching calendar date over the index fallback", () => {
    const envelope = {
      days: [
        { date: "2026-04-20", pillars: {} },
        { date: "2026-04-21", pillars: {} },
        { date: "2026-04-22", pillars: {} },
      ],
    };
    const now = new Date(2026, 3, 22);
    const out = resolveTodayDay(envelope, 0, now);
    expect(out.dayIndex).toBe(2);
    expect(out.day?.date).toBe("2026-04-22");
  });

  it("falls back to the provided index when no calendar match exists", () => {
    const envelope = {
      days: [
        { date: "2026-04-20", pillars: {} },
        { date: "2026-04-21", pillars: {} },
      ],
    };
    const now = new Date(2026, 3, 25);
    const out = resolveTodayDay(envelope, 1, now);
    expect(out.dayIndex).toBe(1);
    expect(out.day?.date).toBe("2026-04-21");
  });

  it("returns nulls when the envelope is missing or empty", () => {
    expect(resolveTodayDay(null, 0)).toEqual({ day: null, dayIndex: null });
    expect(resolveTodayDay({ days: [] }, 0)).toEqual({ day: null, dayIndex: null });
  });
});

describe("pillarTasks", () => {
  it("is case-insensitive", () => {
    const day = {
      date: "2026-04-22",
      pillars: { mind: [{ id: 1, task: "x", context_reason: "", completed: false }] },
    };
    expect(pillarTasks(day, "Mind")).toHaveLength(1);
    expect(pillarTasks(day, "MIND")).toHaveLength(1);
    expect(pillarTasks(day, "Fuel")).toEqual([]);
  });
});

describe("task aggregates", () => {
  const tasks = [
    { id: 1, task: "a", context_reason: "", completed: true },
    { id: 2, task: "b", context_reason: "", completed: false },
    { id: 3, task: "c", context_reason: "", completed: false },
  ];
  it("counts and finds in the right order", () => {
    expect(countDone(tasks)).toBe(1);
    expect(firstOpenTask(tasks)?.id).toBe(2);
    expect(allDone(tasks)).toBe(false);
    expect(allDone([{ id: 1, task: "a", context_reason: "", completed: true }])).toBe(true);
    expect(allDone([])).toBe(false);
  });
});

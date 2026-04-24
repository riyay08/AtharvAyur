import { describe, expect, it } from "vitest";

import { buildAssessment, pickDominantDosha, progressPercent } from "./quizScoring.js";

const QUESTIONS = [
  { id: "q1", section: "Body", prompt: "Build?", options: { a: "thin", b: "medium", c: "heavy" } },
  { id: "q2", section: "Mind", prompt: "Mood?", options: { a: "anxious", b: "sharp", c: "calm" } },
  { id: "q3", section: "Sleep", prompt: "Sleep?", options: { a: "light", b: "moderate", c: "deep" } },
];

const MAP = { a: "vata", b: "pitta", c: "kapha" };

describe("buildAssessment", () => {
  it("scores each answer once and records raw option text", () => {
    const out = buildAssessment(QUESTIONS, { q1: "a", q2: "b", q3: "c" }, MAP);
    expect(out.scores).toEqual({ vata: 1, pitta: 1, kapha: 1 });
    expect(out.rawQuizData).toEqual({ q1: "thin", q2: "sharp", q3: "deep" });
  });

  it("ignores unanswered questions and unknown option keys", () => {
    const out = buildAssessment(QUESTIONS, { q1: "a", q2: "zz" }, MAP);
    expect(out.scores).toEqual({ vata: 1, pitta: 0, kapha: 0 });
    expect(out.rawQuizData).toEqual({ q1: "thin" });
  });

  it("picks a dominant dosha reflecting the highest count", () => {
    const out = buildAssessment(QUESTIONS, { q1: "c", q2: "c", q3: "a" }, MAP);
    expect(out.dominantDosha).toBe("kapha");
  });
});

describe("pickDominantDosha", () => {
  it("breaks ties using vata > pitta > kapha", () => {
    expect(pickDominantDosha({ vata: 2, pitta: 2, kapha: 2 })).toBe("vata");
    expect(pickDominantDosha({ vata: 0, pitta: 3, kapha: 3 })).toBe("pitta");
  });
});

describe("progressPercent", () => {
  it("returns an integer between 0 and 100", () => {
    expect(progressPercent(0, 35)).toBe(0);
    expect(progressPercent(35, 35)).toBe(100);
    expect(progressPercent(18, 35)).toBe(51);
  });

  it("handles invalid totals defensively", () => {
    expect(progressPercent(5, 0)).toBe(0);
    expect(progressPercent(5, Number.NaN)).toBe(0);
  });
});

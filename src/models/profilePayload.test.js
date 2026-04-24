import { describe, expect, it } from "vitest";

import { buildProfilePayload } from "./profilePayload.js";

const QUESTIONS = [
  { id: "q1", section: "Body", prompt: "Build?", options: { a: "thin", b: "heavy" } },
  { id: "q2", section: "Mind", prompt: "Mood?", options: { a: "anxious", b: "calm" } },
];

describe("buildProfilePayload", () => {
  it("captures assessment, selected answers, and consent flags", () => {
    const payload = buildProfilePayload(
      {
        dominantDosha: "vata",
        scores: { vata: 2, pitta: 0, kapha: 0 },
        rawQuizData: { q1: "thin", q2: "anxious" },
      },
      { q1: "a", q2: "a" },
      QUESTIONS,
      { completedAt: "2026-04-22T00:00:00.000Z" }
    );

    expect(payload.consent_flags).toEqual({ prakriti_quiz_completed: true, app: "holistica_web" });
    expect(payload.prakriti_quiz.dominant_dosha).toBe("vata");
    expect(payload.prakriti_quiz.dosha_distribution).toEqual({ vata: 2, pitta: 0, kapha: 0 });
    expect(payload.prakriti_quiz.completed_at).toBe("2026-04-22T00:00:00.000Z");
    expect(payload.prakriti_quiz.selected_answers).toEqual([
      {
        question_id: "q1",
        question_text: "Build?",
        selected_option_key: "a",
        selected_option_text: "thin",
      },
      {
        question_id: "q2",
        question_text: "Mood?",
        selected_option_key: "a",
        selected_option_text: "anxious",
      },
    ]);
  });

  it("records null for unanswered questions", () => {
    const payload = buildProfilePayload(
      {
        dominantDosha: "pitta",
        scores: { vata: 0, pitta: 1, kapha: 0 },
        rawQuizData: { q1: "heavy" },
      },
      { q1: "b" },
      QUESTIONS
    );
    expect(payload.prakriti_quiz.selected_answers[1]).toEqual({
      question_id: "q2",
      question_text: "Mood?",
      selected_option_key: null,
      selected_option_text: null,
    });
  });
});

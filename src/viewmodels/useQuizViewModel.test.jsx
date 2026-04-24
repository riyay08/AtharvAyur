import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useQuizViewModel } from "./useQuizViewModel.js";

const QUESTIONS = [
  { id: "q1", section: "S", prompt: "one", options: { a: "A1", b: "B1" } },
  { id: "q2", section: "S", prompt: "two", options: { a: "A2", b: "B2" } },
  { id: "q3", section: "S", prompt: "three", options: { a: "A3", b: "B3" } },
];

const DOSHA_MAP = { a: "vata", b: "kapha" };

function setup(overrides = {}) {
  const upsertProfile = overrides.upsertProfile ?? vi.fn().mockResolvedValue({ user_id: "u-1" });
  const onProfileSaved = overrides.onProfileSaved ?? vi.fn();
  const autoAdvanceMs = overrides.autoAdvanceMs ?? 0;
  const hook = renderHook(() =>
    useQuizViewModel({
      questions: QUESTIONS,
      doshaMap: DOSHA_MAP,
      upsertProfile,
      onProfileSaved,
      autoAdvanceMs,
    })
  );
  return { ...hook, upsertProfile, onProfileSaved };
}

describe("useQuizViewModel", () => {
  it("walks through questions and transitions to results", () => {
    const { result } = setup();
    expect(result.current.route).toBe("quiz");
    expect(result.current.progress).toBe(0);

    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    expect(result.current.questionIndex).toBe(1);

    act(() => result.current.selectAnswer("b"));
    act(() => result.current.goNext());
    expect(result.current.questionIndex).toBe(2);
    expect(result.current.isLastQuestion).toBe(true);

    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());

    expect(result.current.route).toBe("results");
    expect(result.current.assessment?.scores).toEqual({ vata: 2, pitta: 0, kapha: 1 });
    expect(result.current.assessment?.dominantDosha).toBe("vata");
  });

  it("refuses to advance without a selected answer", () => {
    const { result } = setup();
    act(() => result.current.goNext());
    expect(result.current.questionIndex).toBe(0);
    expect(result.current.route).toBe("quiz");
  });

  it("submitProfile calls the upserter and fires onProfileSaved on success", async () => {
    const { result, upsertProfile, onProfileSaved } = setup();
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());

    await act(async () => {
      await result.current.submitProfile();
    });

    expect(upsertProfile).toHaveBeenCalledTimes(1);
    expect(onProfileSaved).toHaveBeenCalledWith({ user_id: "u-1" });
    expect(result.current.submitError).toBeNull();
    expect(result.current.submitting).toBe(false);
  });

  it("submitProfile surfaces errors", async () => {
    const upsertProfile = vi.fn().mockRejectedValue(new Error("nope"));
    const { result } = setup({ upsertProfile });
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());

    await act(async () => {
      await result.current.submitProfile();
    });

    expect(result.current.submitError).toBe("nope");
  });

  it("reset returns to the first question with no answers", () => {
    const { result } = setup();
    act(() => result.current.selectAnswer("a"));
    act(() => result.current.goNext());
    act(() => result.current.reset());
    expect(result.current.questionIndex).toBe(0);
    expect(result.current.answers).toEqual({});
    expect(result.current.route).toBe("quiz");
  });

  it("auto-advances to the next question after the user picks an option", () => {
    vi.useFakeTimers();
    try {
      const { result } = setup({ autoAdvanceMs: 200 });

      act(() => result.current.selectAnswer("a"));
      expect(result.current.questionIndex).toBe(0);

      act(() => {
        vi.advanceTimersByTime(199);
      });
      expect(result.current.questionIndex).toBe(0);

      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(result.current.questionIndex).toBe(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it("auto-advances into results on the final question", () => {
    vi.useFakeTimers();
    try {
      const { result } = setup({ autoAdvanceMs: 100 });

      act(() => result.current.selectAnswer("a"));
      act(() => vi.runAllTimers());
      act(() => result.current.selectAnswer("a"));
      act(() => vi.runAllTimers());
      act(() => result.current.selectAnswer("a"));
      act(() => vi.runAllTimers());

      expect(result.current.route).toBe("results");
      expect(result.current.assessment?.dominantDosha).toBe("vata");
    } finally {
      vi.useRealTimers();
    }
  });

  it("skipQuestion advances without recording an answer", () => {
    const { result } = setup();
    act(() => result.current.skipQuestion());
    expect(result.current.questionIndex).toBe(1);
    expect(result.current.answers).toEqual({});
    act(() => result.current.skipQuestion());
    act(() => result.current.skipQuestion());
    expect(result.current.route).toBe("results");
    expect(result.current.assessment?.scores).toEqual({ vata: 0, pitta: 0, kapha: 0 });
  });

  it("skipAssessment posts a skipped profile and notifies the caller", async () => {
    const upsertProfile = vi.fn().mockResolvedValue({ user_id: "u-skip" });
    const onProfileSaved = vi.fn();
    const { result } = setup({ upsertProfile, onProfileSaved });

    act(() => result.current.selectAnswer("a"));
    await act(async () => {
      await result.current.skipAssessment();
    });

    expect(upsertProfile).toHaveBeenCalledTimes(1);
    const payload = upsertProfile.mock.calls[0][0];
    expect(payload.consent_flags.prakriti_quiz_skipped).toBe(true);
    expect(payload.consent_flags.prakriti_quiz_completed).toBe(false);
    expect(payload.prakriti_quiz).toBeDefined();
    expect(onProfileSaved).toHaveBeenCalledWith({ user_id: "u-skip" });
    expect(result.current.submitError).toBeNull();
  });

  it("re-selecting before the timer fires keeps the latest choice", () => {
    vi.useFakeTimers();
    try {
      const { result } = setup({ autoAdvanceMs: 200 });

      act(() => result.current.selectAnswer("a"));
      act(() => result.current.selectAnswer("b"));
      act(() => vi.runAllTimers());

      expect(result.current.questionIndex).toBe(1);
      expect(result.current.answers).toEqual({ q1: "b" });
    } finally {
      vi.useRealTimers();
    }
  });
});

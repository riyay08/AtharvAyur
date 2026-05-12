import { describe, expect, it } from "vitest";

import {
  CHAPTER_START_INDICES,
  getChapterProgress,
  interstitialSlotAfterQuestion,
  shouldShowInterstitialAfter,
  usesStandardChapters,
} from "./quizChapters.js";

describe("quizChapters", () => {
  it("splits 35 questions into four chapters", () => {
    expect(CHAPTER_START_INDICES).toEqual([0, 8, 17, 26]);
    const sizes = CHAPTER_START_INDICES.map((start) => getChapterProgress(start, 35).chapterSize);
    expect(sizes).toEqual([8, 9, 9, 9]);
    expect(sizes.reduce((a, b) => a + b, 0)).toBe(35);
  });

  it("flags interstitial boundaries", () => {
    expect(shouldShowInterstitialAfter(7, 35)).toBe(true);
    expect(shouldShowInterstitialAfter(8, 35)).toBe(false);
    expect(interstitialSlotAfterQuestion(7, 35)).toBe(1);
    expect(interstitialSlotAfterQuestion(16, 35)).toBe(2);
    expect(interstitialSlotAfterQuestion(25, 35)).toBe(3);
  });

  it("disables milestones for non-standard lengths", () => {
    expect(usesStandardChapters(3)).toBe(false);
    expect(shouldShowInterstitialAfter(7, 3)).toBe(false);
  });
});

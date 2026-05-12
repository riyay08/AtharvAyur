/**
 * Four-chapter layout for the standard 35-question dosha flow.
 * Used for milestone UI only; question order stays canonical from `quizI18n`.
 */

export const QUIZ_STANDARD_LENGTH = 35;

/** Inclusive start index per chapter (0-based). */
export const CHAPTER_START_INDICES = [0, 8, 17, 26];

/** Last question index of chapters 1–3 (show interstitial after answering these). */
export const CHAPTER_END_BEFORE_INTERSTITIAL = [7, 16, 25];

/**
 * @param {number} totalQuestions
 * @returns {boolean}
 */
export function usesStandardChapters(totalQuestions) {
  return totalQuestions === QUIZ_STANDARD_LENGTH;
}

/**
 * @param {number} questionIndex 0-based
 * @param {number} totalQuestions
 * @returns {{ chapterIndex: number, indexInChapter: number, chapterSize: number }}
 */
export function getChapterProgress(questionIndex, totalQuestions) {
  if (!usesStandardChapters(totalQuestions)) {
    return {
      chapterIndex: 0,
      indexInChapter: questionIndex,
      chapterSize: totalQuestions,
    };
  }
  let chapterIndex = 0;
  for (let i = CHAPTER_START_INDICES.length - 1; i >= 0; i -= 1) {
    if (questionIndex >= CHAPTER_START_INDICES[i]) {
      chapterIndex = i;
      break;
    }
  }
  const start = CHAPTER_START_INDICES[chapterIndex];
  const endExclusive =
    chapterIndex < CHAPTER_START_INDICES.length - 1
      ? CHAPTER_START_INDICES[chapterIndex + 1]
      : totalQuestions;
  return {
    chapterIndex,
    indexInChapter: questionIndex - start,
    chapterSize: endExclusive - start,
  };
}

/**
 * After the user completes this question index (still on that question), show interstitial before the next.
 * @param {number} questionIndex
 * @param {number} totalQuestions
 */
export function shouldShowInterstitialAfter(questionIndex, totalQuestions) {
  if (!usesStandardChapters(totalQuestions)) return false;
  return CHAPTER_END_BEFORE_INTERSTITIAL.includes(questionIndex);
}

/**
 * Which interstitial copy block to show (1 = after Ch1, 2 = after Ch2, 3 = after Ch3).
 * @param {number} questionIndex last answered index
 * @param {number} totalQuestions
 * @returns {1|2|3|null}
 */
export function interstitialSlotAfterQuestion(questionIndex, totalQuestions) {
  if (!shouldShowInterstitialAfter(questionIndex, totalQuestions)) return null;
  const i = CHAPTER_END_BEFORE_INTERSTITIAL.indexOf(questionIndex);
  return /** @type {const} */ (i + 1);
}

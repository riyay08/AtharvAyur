/**
 * Backwards-compatible exports for the quiz dataset.
 *
 * Localized question/option strings now live in `src/i18n/quizI18n.js`
 * and are consumed via `getLocalizedQuestions(language)`. The exports
 * below keep the legacy English shape for any caller (tests, scoring,
 * profile payload helpers) that still imports from this module.
 *
 * - `DOSHA_MAP` is language-independent (option key → dosha).
 * - `DOSHA_LABELS` and `DOSHA_SUMMARIES` are kept in English for
 *   non-React utilities; the UI prefers `t("quiz.doshaLabels.*")`.
 * - `QUIZ_QUESTIONS` is the English-localized array (built once).
 */

import { getLocalizedQuestions } from "../i18n/quizI18n.js";

export const DOSHA_MAP = {
  a: "vata",
  b: "pitta",
  c: "kapha",
};

export const DOSHA_LABELS = {
  vata: "Vata",
  pitta: "Pitta",
  kapha: "Kapha",
};

export const DOSHA_SUMMARIES = {
  vata:
    "Your profile leans Vata. You likely thrive with steady routines, grounding meals, warmth, and intentional wind-down rituals that calm a highly active mind.",
  pitta:
    "Your profile leans Pitta. You likely do best with balanced intensity, cooling habits, and sustainable structure that channels ambition without overheating body or mind.",
  kapha:
    "Your profile leans Kapha. You likely benefit from energizing movement, lighter stimulation, and momentum-building routines that keep motivation and metabolism active.",
};

export const QUIZ_QUESTIONS = getLocalizedQuestions("en");

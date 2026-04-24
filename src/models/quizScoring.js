/**
 * Pure prakriti-quiz scoring. No React, no I/O. Given the question bank and
 * user answers, returns dosha scores, dominant dosha, and structured raw data
 * for persistence.
 *
 * @typedef {'vata'|'pitta'|'kapha'} Dosha
 * @typedef {{ vata: number, pitta: number, kapha: number }} DoshaScores
 *
 * @typedef {Object} QuizQuestion
 * @property {string} id
 * @property {string} section
 * @property {string} prompt
 * @property {Record<string,string>} options  // key -> display text
 *
 * @typedef {Object} Assessment
 * @property {Dosha} dominantDosha
 * @property {DoshaScores} scores
 * @property {Record<string,string>} rawQuizData  // questionId -> option text
 */

const EMPTY_SCORES = Object.freeze({ vata: 0, pitta: 0, kapha: 0 });

/**
 * @param {QuizQuestion[]} questions
 * @param {Record<string,string>} answers - questionId -> option key
 * @param {Record<string,Dosha>} optionToDosha - option key -> dosha
 * @returns {Assessment}
 */
export function buildAssessment(questions, answers, optionToDosha) {
  const scores = { ...EMPTY_SCORES };
  /** @type {Record<string,string>} */
  const rawQuizData = {};

  for (const q of questions) {
    const selectedKey = answers[q.id];
    if (!selectedKey) continue;
    const dosha = optionToDosha[selectedKey];
    if (dosha && scores[dosha] != null) scores[dosha] += 1;
    if (q.options[selectedKey] != null) rawQuizData[q.id] = q.options[selectedKey];
  }

  return {
    dominantDosha: pickDominantDosha(scores),
    scores,
    rawQuizData,
  };
}

/**
 * Ties are broken by a stable priority: vata > pitta > kapha.
 * @param {DoshaScores} scores
 * @returns {Dosha}
 */
export function pickDominantDosha(scores) {
  const order = /** @type {const} */ (["vata", "pitta", "kapha"]);
  let best = order[0];
  for (const d of order) {
    if (scores[d] > scores[best]) best = d;
  }
  return best;
}

/**
 * Progress %, clamped 0–100, rounded to integer.
 * @param {number} answered
 * @param {number} total
 */
export function progressPercent(answered, total) {
  if (!Number.isFinite(total) || total <= 0) return 0;
  const pct = (answered / total) * 100;
  if (pct < 0) return 0;
  if (pct > 100) return 100;
  return Math.round(pct);
}

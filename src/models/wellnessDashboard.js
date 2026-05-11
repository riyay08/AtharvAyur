/**
 * Pure helpers for the wellness hub Overview dashboard (from GET /profile/me).
 */

import {
  countDone,
  dayIndexForToday,
  isEnvelope,
  localYmd,
  pillarTasks,
  resolveTodayDay,
} from "./planShape.js";

/**
 * @param {unknown} healthProfile - API health_profile object or null
 * @returns {'vata'|'pitta'|'kapha'|null}
 */
export function extractDominantDosha(healthProfile) {
  const c = healthProfile?.conditions;
  if (!c || typeof c !== "object" || Array.isArray(c)) return null;
  const pq = /** @type {Record<string, unknown>} */ (c).prakriti_quiz;
  if (!pq || typeof pq !== "object") return null;
  const raw = /** @type {Record<string, unknown>} */ (pq).dominant_dosha;
  if (typeof raw !== "string") return null;
  const v = raw.toLowerCase();
  return v === "vata" || v === "pitta" || v === "kapha" ? v : null;
}

/**
 * @param {{ check_in_date?: string } | null | undefined} latest
 * @param {Date} [now]
 */
export function checkInIsToday(latest, now = new Date()) {
  if (!latest?.check_in_date) return false;
  return String(latest.check_in_date) === localYmd(now);
}

/**
 * @param {unknown} tasks
 * @param {string} startDateStr YYYY-MM-DD
 * @param {Date} [now]
 * @returns {{ done: number, total: number } | null}
 */
export function todayPlanTaskCounts(tasks, startDateStr, now = new Date()) {
  if (!tasks || !startDateStr || !isEnvelope(tasks)) return null;
  const fallbackIndex = dayIndexForToday(startDateStr, now);
  const { day } = resolveTodayDay(tasks, fallbackIndex, now);
  if (!day?.pillars || typeof day.pillars !== "object") return null;
  let total = 0;
  let done = 0;
  for (const k of Object.keys(day.pillars)) {
    const ts = pillarTasks(day, k);
    total += ts.length;
    done += countDone(ts);
  }
  return total > 0 ? { done, total } : null;
}

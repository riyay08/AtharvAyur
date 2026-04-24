/**
 * Pure plan-shape helpers: identify envelope format, resolve today's day,
 * extract pillar tasks case-insensitively. No React, no I/O.
 *
 * @typedef {{ id: number, task: string, context_reason: string, completed: boolean }} PlanTask
 * @typedef {{ date: string, pillars: Record<string, PlanTask[]> }} PlanDay
 * @typedef {{ daily_focus_message?: string, days?: PlanDay[] }} PlanEnvelope
 */

/** @param {Date} [now] */
export function localYmd(now = new Date()) {
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** @param {unknown} tasks */
export function isEnvelope(tasks) {
  return (
    tasks != null &&
    typeof tasks === "object" &&
    !Array.isArray(tasks) &&
    Array.isArray(/** @type {PlanEnvelope} */ (tasks).days)
  );
}

/**
 * Day index (0–6) if today falls inside the plan's week, else null.
 * @param {string} startDateStr - YYYY-MM-DD
 * @param {Date} [now]
 */
export function dayIndexForToday(startDateStr, now = new Date()) {
  if (!startDateStr) return null;
  const parts = startDateStr.split("-").map(Number);
  if (parts.length < 3 || parts.some((n) => !Number.isFinite(n))) return null;
  const [y, m, d] = parts;
  const start = new Date(y, m - 1, d);
  const t0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.round((t0.getTime() - start.getTime()) / 86400000);
  if (diffDays < 0 || diffDays > 6) return null;
  return diffDays;
}

/**
 * Locate the day entry whose `date` matches today, else fall back to the
 * provided week-day index (if valid), else null.
 * @param {PlanEnvelope | null} envelope
 * @param {number | null} fallbackIndex
 * @param {Date} [now]
 * @returns {{ day: PlanDay | null, dayIndex: number | null }}
 */
export function resolveTodayDay(envelope, fallbackIndex, now = new Date()) {
  const days = envelope?.days;
  if (!Array.isArray(days) || days.length === 0) return { day: null, dayIndex: null };
  const target = localYmd(now);
  const idx = days.findIndex((x) => x && x.date === target);
  if (idx >= 0) return { day: days[idx], dayIndex: idx };
  if (fallbackIndex != null && days[fallbackIndex]) {
    return { day: days[fallbackIndex], dayIndex: fallbackIndex };
  }
  return { day: null, dayIndex: null };
}

/**
 * Case-insensitive lookup of a pillar's task list.
 * @param {PlanDay | null} day
 * @param {string} pillarKey
 * @returns {PlanTask[]}
 */
export function pillarTasks(day, pillarKey) {
  const p = day?.pillars;
  if (!p || typeof p !== "object") return [];
  if (Array.isArray(p[pillarKey])) return p[pillarKey];
  const want = pillarKey.toLowerCase();
  for (const k of Object.keys(p)) {
    if (typeof k === "string" && k.toLowerCase() === want && Array.isArray(p[k])) {
      return p[k];
    }
  }
  return [];
}

/** @param {PlanTask[]} tasks */
export function countDone(tasks) {
  return tasks.reduce((n, t) => n + (t.completed ? 1 : 0), 0);
}

/** @param {PlanTask[]} tasks */
export function firstOpenTask(tasks) {
  return tasks.find((t) => !t.completed) ?? null;
}

/** @param {PlanTask[]} tasks */
export function allDone(tasks) {
  return tasks.length > 0 && tasks.every((t) => t.completed);
}

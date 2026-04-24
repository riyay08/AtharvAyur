/**
 * Pure helpers for the daily check-in feature. No React, no I/O.
 */

export const SLEEP_VALUES = /** @type {const} */ (["heavy", "restless", "refreshed"]);
export const DIGESTION_VALUES = /** @type {const} */ (["bloated", "acidic", "calm"]);
export const ENERGY_VALUES = /** @type {const} */ (["wired", "grounded", "sluggish"]);
export const MOVEMENT_VALUES = /** @type {const} */ (["rest", "light", "sweat"]);

/** Ordered for the slider control. */
export const ENERGY_ORDER = ENERGY_VALUES;

export const DEFAULT_FORM = Object.freeze({
  sleepQuality: "refreshed",
  digestion: "calm",
  energyState: "grounded",
  movement: "light",
  water: 0,
});

/** @param {Date} [d] */
export function localYmd(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Normalize backend ISO timestamp or date to YYYY-MM-DD. */
export function normalizeYmd(iso) {
  if (iso == null) return "";
  const s = String(iso);
  return s.length >= 10 ? s.slice(0, 10) : s;
}

/**
 * Reduce API record → form state (safe defaults on unknown enums).
 * @param {null | Record<string, unknown>} rec
 */
export function formFromRecord(rec) {
  if (!rec || typeof rec !== "object") return { ...DEFAULT_FORM };
  const sq = rec.sleep_quality;
  const dg = rec.digestion;
  const es = rec.energy_state;
  const mv = rec.movement;
  const w = rec.water_glasses;
  return {
    sleepQuality: SLEEP_VALUES.includes(sq) ? sq : DEFAULT_FORM.sleepQuality,
    digestion: DIGESTION_VALUES.includes(dg) ? dg : DEFAULT_FORM.digestion,
    energyState: ENERGY_VALUES.includes(es) ? es : DEFAULT_FORM.energyState,
    movement: MOVEMENT_VALUES.includes(mv) ? mv : DEFAULT_FORM.movement,
    water: typeof w === "number" && w >= 0 ? w : 0,
  };
}

/**
 * @param {string} ymd - YYYY-MM-DD
 * @returns {{ weekday: string, dayNum: number }}
 */
export function dayLabel(ymd) {
  const [y, m, d] = ymd.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return {
    weekday: dt.toLocaleDateString(undefined, { weekday: "short" }),
    dayNum: d,
  };
}

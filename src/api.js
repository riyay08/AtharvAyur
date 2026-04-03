/** HolisticAI Health backend — use VITE_API_URL or dev proxy `/api` → FastAPI :8000 */

const USER_STORAGE_KEY = "holistica_user_id";

export function getStoredUserId() {
  try {
    return localStorage.getItem(USER_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredUserId(id) {
  try {
    localStorage.setItem(USER_STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

export function clearStoredUserId() {
  try {
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

/** Clears saved user id + onboarding flag (e.g. to show the quiz again). */
export function clearHolisticaSession() {
  clearStoredUserId();
  try {
    localStorage.removeItem("holistica_has_completed_onboarding");
  } catch {
    /* ignore */
  }
}

function apiBase() {
  const raw = import.meta.env.VITE_API_URL;
  if (raw != null && String(raw).trim() !== "") {
    return String(raw).replace(/\/$/, "");
  }
  return "";
}

function apiUrl(path) {
  const base = apiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : `/api${p}`;
}

function formatError(status, body) {
  if (!body || typeof body !== "object") return `Request failed (${status})`;
  const { detail, message } = body;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d.msg ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (message) return String(message);
  return `Request failed (${status})`;
}

/**
 * @param {object} payload - ProfileUpsertRequest shape (optional user_id for updates)
 */
export async function upsertProfile(payload) {
  const res = await fetch(apiUrl("/profile"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {string} userId - UUID
 * @param {string} message
 */
export async function sendChatMessage(userId, message) {
  const res = await fetch(apiUrl("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {string} userId
 * @param {{
 *   check_in_date?: string,
 *   sleep_quality: 'heavy'|'restless'|'refreshed',
 *   digestion: 'bloated'|'acidic'|'calm',
 *   energy_state: 'wired'|'grounded'|'sluggish',
 *   movement: 'rest'|'light'|'sweat',
 *   water_glasses: number
 * }} payload
 */
export async function postCheckIn(userId, payload) {
  const res = await fetch(apiUrl("/checkin"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, ...payload }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {string} userId
 * @param {string} [endDateYmd] - Client local YYYY-MM-DD for window end (today); aligns 7-day strip with UI.
 */
export async function getCheckInWeek(userId, endDateYmd) {
  const q = new URLSearchParams({ user_id: userId });
  if (endDateYmd) q.set("end_date", endDateYmd);
  const res = await fetch(`${apiUrl("/checkin/week")}?${q}`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/** @param {string} userId */
export async function getCurrentPlan(userId) {
  const q = new URLSearchParams({ user_id: userId });
  const res = await fetch(`${apiUrl("/plan/current")}?${q}`);
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(formatError(res.status, data || {}));
  return data;
}

/**
 * @param {{ user_id: string, plan_id?: string | null, day_index: number, pillar: 'Mind'|'Fuel'|'Body', task_id: number, completed?: boolean | null }} body
 */
export async function putPlanTask(body) {
  const res = await fetch(apiUrl("/plan/task"), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/** @param {string} userId */
export async function generateWeeklyPlan(userId) {
  const res = await fetch(apiUrl("/plan/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

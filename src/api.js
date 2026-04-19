/** HolisticAI Health backend — use VITE_API_URL or dev proxy `/api` → FastAPI :8000 */

const USER_STORAGE_KEY = "holistica_user_id";
const ACCESS_TOKEN_KEY = "holistica_access_token";

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

export function getStoredAccessToken() {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredAccessToken(token) {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearStoredAccessToken() {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

/** Clears saved user id, JWT, and onboarding flag (e.g. to show the quiz again). */
export function clearHolisticaSession() {
  clearStoredUserId();
  clearStoredAccessToken();
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

let _sessionInFlight = null;

/**
 * Ensures a JWT exists (creates a user when none is stored, or re-mints for stored user id).
 * Safe to call from multiple components concurrently.
 */
export async function ensureSession() {
  if (getStoredAccessToken()) return;
  if (!_sessionInFlight) {
    _sessionInFlight = (async () => {
      const attempt = async (body) => {
        const res = await fetch(apiUrl("/auth/token"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        return { res, data };
      };

      let body = {};
      const sid = getStoredUserId();
      if (sid) body.user_id = sid;
      let { res, data } = await attempt(body);
      if (res.status === 404 && sid) {
        clearStoredUserId();
        ({ res, data } = await attempt({}));
      }
      if (!res.ok) throw new Error(formatError(res.status, data));
      setStoredAccessToken(data.access_token);
      if (data.user_id) setStoredUserId(String(data.user_id));
    })().finally(() => {
      _sessionInFlight = null;
    });
  }
  await _sessionInFlight;
}

function authHeaders() {
  const t = getStoredAccessToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function jsonHeadersWithAuth() {
  return { "Content-Type": "application/json", ...authHeaders() };
}

/**
 * @param {object} payload - ProfileUpsertRequest shape
 */
export async function upsertProfile(payload) {
  await ensureSession();
  const res = await fetch(apiUrl("/profile"), {
    method: "POST",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {string} message
 * @param {{ latitude?: number, longitude?: number }} [coords]
 */
export async function sendChatMessage(message, coords) {
  await ensureSession();
  const body = { message };
  if (
    coords &&
    typeof coords.latitude === "number" &&
    typeof coords.longitude === "number"
  ) {
    body.latitude = coords.latitude;
    body.longitude = coords.longitude;
  }
  const res = await fetch(apiUrl("/chat"), {
    method: "POST",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {{
 *   check_in_date?: string,
 *   sleep_quality: 'heavy'|'restless'|'refreshed',
 *   digestion: 'bloated'|'acidic'|'calm',
 *   energy_state: 'wired'|'grounded'|'sluggish',
 *   movement: 'rest'|'light'|'sweat',
 *   water_glasses: number
 * }} payload
 */
export async function postCheckIn(payload) {
  await ensureSession();
  const res = await fetch(apiUrl("/checkin"), {
    method: "POST",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * Cached daily environment tip (per user, per UTC day on server).
 * @param {number} latitude
 * @param {number} longitude
 */
export async function postEnvironmentDailyTip(latitude, longitude) {
  await ensureSession();
  const res = await fetch(apiUrl("/environment/daily-tip"), {
    method: "POST",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify({
      latitude,
      longitude,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

/**
 * @param {string} [endDateYmd] - Client local YYYY-MM-DD for window end (today); aligns 7-day strip with UI.
 */
export async function getCheckInWeek(endDateYmd) {
  await ensureSession();
  const q = new URLSearchParams();
  if (endDateYmd) q.set("end_date", endDateYmd);
  const qs = q.toString();
  const url = qs ? `${apiUrl("/checkin/week")}?${qs}` : apiUrl("/checkin/week");
  const res = await fetch(url, { headers: authHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

export async function getCurrentPlan() {
  await ensureSession();
  const res = await fetch(apiUrl("/plan/current"), { headers: authHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data || {}));
  return data;
}

/**
 * @param {{ plan_id?: string | null, day_index: number, pillar: 'Mind'|'Fuel'|'Body', task_id: number, completed?: boolean | null }} body
 */
export async function putPlanTask(body) {
  await ensureSession();
  const res = await fetch(apiUrl("/plan/task"), {
    method: "PUT",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

export async function generateWeeklyPlan() {
  await ensureSession();
  const res = await fetch(apiUrl("/plan/generate"), {
    method: "POST",
    headers: jsonHeadersWithAuth(),
    body: JSON.stringify({}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(res.status, data));
  return data;
}

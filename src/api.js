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

/**
 * HTTP client: base URL resolution, auth headers, and unified error mapping.
 * All feature services go through `request()`.
 */

import { getStoredAccessToken } from "./storage.js";

function apiBase() {
  const raw = import.meta.env.VITE_API_URL;
  if (raw != null && String(raw).trim() !== "") {
    return String(raw).replace(/\/$/, "");
  }
  return "";
}

/** @param {string} path */
export function apiUrl(path) {
  const base = apiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : `/api${p}`;
}

/**
 * Formats a backend error body into a human-readable message.
 * @param {number} status
 * @param {unknown} body
 */
export function formatError(status, body) {
  if (!body || typeof body !== "object") return `Request failed (${status})`;
  const detail = /** @type {any} */ (body).detail;
  const message = /** @type {any} */ (body).message;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (message) return String(message);
  return `Request failed (${status})`;
}

/** @returns {Record<string, string>} */
export function authHeaders() {
  const t = getStoredAccessToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/**
 * Thin wrapper around `fetch` that:
 *   - Prefixes path with `apiBase`
 *   - Parses JSON safely (tolerates empty bodies)
 *   - Throws an Error with a friendly message on non-2xx
 *
 * @param {string} path
 * @param {RequestInit & { json?: unknown, auth?: boolean }} [opts]
 * @returns {Promise<any>}
 */
export async function request(path, opts = {}) {
  const { json, auth = true, headers, ...rest } = opts;
  const finalHeaders = { ...(headers || {}) };
  if (json !== undefined) {
    finalHeaders["Content-Type"] = "application/json";
  }
  if (auth) Object.assign(finalHeaders, authHeaders());

  const res = await fetch(apiUrl(path), {
    ...rest,
    headers: finalHeaders,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(formatError(res.status, data));
    /** @type {any} */ (err).status = res.status;
    /** @type {any} */ (err).body = data;
    throw err;
  }
  return data;
}

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
  if (body != null && typeof body !== "object") {
    return `Request failed (${status})`;
  }
  if (!body || typeof body !== "object") return `Request failed (${status})`;
  const detail = /** @type {any} */ (body).detail;
  const message = /** @type {any} */ (body).message;
  if (typeof detail === "string") return detail;
  if (typeof detail === "number" || typeof detail === "boolean") return String(detail);
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (detail != null && typeof detail === "object") {
    try {
      const s = JSON.stringify(detail);
      if (s !== "{}") return `Request failed (${status}): ${s}`;
    } catch {
      /* ignore */
    }
  }
  if (message) return String(message);
  try {
    const s = JSON.stringify(body);
    if (s !== "{}") return `Request failed (${status}): ${s}`;
  } catch {
    /* ignore */
  }
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

  const url = apiUrl(path);
  let res;
  try {
    res = await fetch(url, {
      ...rest,
      headers: finalHeaders,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch (e) {
    const base = apiBase();
    const isNetwork =
      e instanceof TypeError ||
      (e instanceof Error && /failed to fetch|load failed|networkerror/i.test(e.message));
    if (isNetwork) {
      const hint = base
        ? `Could not reach the API at ${url}. Check VITE_API_URL in .env, CORS on the server, and that the API is running.`
        : `Could not reach the API (${url}). Start the backend on port 8000: open a second terminal and run "cd backend && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000", or from the project root run "npm run dev:full".`;
      throw new Error(hint);
    }
    throw e;
  }

  const rawText = await res.text();
  let data = {};
  if (rawText) {
    try {
      data = JSON.parse(rawText);
    } catch {
      if (!res.ok) {
        const err = new Error(
          rawText.length > 240 ? `Request failed (${res.status}): ${rawText.slice(0, 240)}…` : `Request failed (${res.status}): ${rawText}`
        );
        /** @type {any} */ (err).status = res.status;
        /** @type {any} */ (err).body = { detail: rawText };
        throw err;
      }
    }
  }
  if (!res.ok) {
    const errMsg = formatError(res.status, data);
    const err = new Error(errMsg);
    /** @type {any} */ (err).status = res.status;
    /** @type {any} */ (err).body = data;
    throw err;
  }
  return data;
}

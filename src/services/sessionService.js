/**
 * Session lifecycle: ensures a JWT exists before any authenticated request.
 * Uses a single in-flight promise so concurrent callers share the same token.
 */

import { request } from "./apiClient.js";
import {
  clearStoredUserId,
  getStoredAccessToken,
  getStoredUserId,
  setStoredAccessToken,
  setStoredUserId,
} from "./storage.js";

let _sessionInFlight = null;

export async function ensureSession() {
  if (getStoredAccessToken()) return;
  if (!_sessionInFlight) {
    _sessionInFlight = (async () => {
      const attempt = async (body) => {
        return request("/auth/token", {
          method: "POST",
          json: body,
          auth: false,
        });
      };

      let body = {};
      const sid = getStoredUserId();
      if (sid) body.user_id = sid;
      try {
        const data = await attempt(body);
        setStoredAccessToken(data.access_token);
        if (data.user_id) setStoredUserId(String(data.user_id));
      } catch (err) {
        if (err && /** @type {any} */ (err).status === 404 && sid) {
          clearStoredUserId();
          const data = await attempt({});
          setStoredAccessToken(data.access_token);
          if (data.user_id) setStoredUserId(String(data.user_id));
        } else {
          throw err;
        }
      }
    })().finally(() => {
      _sessionInFlight = null;
    });
  }
  await _sessionInFlight;
}

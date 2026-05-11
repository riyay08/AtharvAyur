import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";

/** @param {object} payload - ProfileUpsertRequest shape */
export async function upsertProfile(payload) {
  await ensureSession();
  return request("/profile", { method: "POST", json: payload });
}

/** Current profile snapshot (health profile, latest check-in, active weekly plan). */
export async function fetchProfileMe() {
  await ensureSession();
  return request("/profile/me", { method: "GET" });
}

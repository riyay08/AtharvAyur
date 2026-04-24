import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";

/** @param {object} payload */
export async function postCheckIn(payload) {
  await ensureSession();
  return request("/checkin", { method: "POST", json: payload });
}

/** @param {string | undefined} endDateYmd - client local YYYY-MM-DD */
export async function getCheckInWeek(endDateYmd) {
  await ensureSession();
  const q = new URLSearchParams();
  if (endDateYmd) q.set("end_date", endDateYmd);
  const qs = q.toString();
  return request(qs ? `/checkin/week?${qs}` : "/checkin/week", { method: "GET" });
}

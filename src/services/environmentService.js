import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";

/**
 * @param {number} latitude
 * @param {number} longitude
 */
export async function postEnvironmentDailyTip(latitude, longitude) {
  await ensureSession();
  return request("/environment/daily-tip", {
    method: "POST",
    json: { latitude, longitude },
  });
}

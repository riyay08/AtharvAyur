import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";

/**
 * @param {string} message
 * @param {{ latitude?: number, longitude?: number } | undefined} coords
 */
export async function sendChatMessage(message, coords) {
  await ensureSession();
  /** @type {Record<string, unknown>} */
  const body = { message };
  if (
    coords &&
    typeof coords.latitude === "number" &&
    typeof coords.longitude === "number"
  ) {
    body.latitude = coords.latitude;
    body.longitude = coords.longitude;
  }
  return request("/chat", { method: "POST", json: body });
}

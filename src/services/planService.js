import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";

export async function getCurrentPlan() {
  await ensureSession();
  return request("/plan/current", { method: "GET" });
}

export async function generateWeeklyPlan() {
  await ensureSession();
  return request("/plan/generate", { method: "POST", json: {} });
}

/**
 * @param {{ plan_id?: string | null, day_index: number, pillar: 'Mind'|'Fuel'|'Body', task_id: number, completed?: boolean | null }} body
 */
export async function putPlanTask(body) {
  await ensureSession();
  return request("/plan/task", { method: "PUT", json: body });
}

import { useCallback, useMemo, useState } from "react";

import { isEnvelope, resolveTodayDay } from "../models/planShape.js";
import { putPlanTask as putPlanTaskApi } from "../services/planService.js";

/**
 * ViewModel for the Mind/Fuel/Body "first-uncompleted-task" stack.
 *
 * @param {{
 *   plan: any,
 *   userId: string | null,
 *   weekDayIndex: number | null,
 *   onPlanUpdated: (plan: any) => void,
 *   onError: (msg: string) => void,
 *   putPlanTask?: typeof putPlanTaskApi,
 *   sleep?: (ms: number) => Promise<void>,
 * }} params
 */
export function useDynamicCategoryStackViewModel({
  plan,
  userId,
  weekDayIndex,
  onPlanUpdated,
  onError,
  putPlanTask = putPlanTaskApi,
  sleep = (ms) => new Promise((r) => setTimeout(r, ms)),
}) {
  const envelope =
    plan?.tasks && typeof plan.tasks === "object" && !Array.isArray(plan.tasks)
      ? plan.tasks
      : null;

  const { day, dayIndex } = useMemo(
    () => resolveTodayDay(envelope, weekDayIndex),
    [envelope, weekDayIndex]
  );

  const [expanded, setExpanded] = useState(/** @type {string | null} */ (null));
  const [slideOut, setSlideOut] =
    useState(/** @type {{ pillar: string, taskId: number } | null} */ (null));
  const [greenKey, setGreenKey] = useState(/** @type {string | null} */ (null));
  const [busy, setBusy] = useState(false);

  const toggleExpand = useCallback((pillarKey, taskId) => {
    const key = `${pillarKey}-${taskId}`;
    setExpanded((prev) => (prev === key ? null : key));
  }, []);

  const completeTask = useCallback(
    async (pillarKey, task) => {
      if (!userId || dayIndex == null || busy || !plan?.id) return;
      const k = `${pillarKey}-${task.id}`;
      setGreenKey(k);
      setSlideOut({ pillar: pillarKey, taskId: task.id });
      await sleep(420);
      try {
        setBusy(true);
        const updated = await putPlanTask({
          plan_id: plan.id,
          day_index: dayIndex,
          pillar: pillarKey,
          task_id: task.id,
          completed: true,
        });
        onPlanUpdated(updated);
        setExpanded(null);
      } catch (e) {
        onError(e instanceof Error ? e.message : "Could not update task.");
        setGreenKey(null);
        setSlideOut(null);
      } finally {
        setBusy(false);
        setSlideOut(null);
        setGreenKey(null);
      }
    },
    [userId, dayIndex, busy, plan?.id, onPlanUpdated, onError, putPlanTask, sleep]
  );

  return {
    envelope,
    day,
    dayIndex,
    focusMessage:
      envelope && typeof envelope.daily_focus_message === "string"
        ? envelope.daily_focus_message
        : "",
    expanded,
    slideOut,
    greenKey,
    busy,
    toggleExpand,
    completeTask,
    isValidEnvelope: isEnvelope(plan?.tasks),
  };
}

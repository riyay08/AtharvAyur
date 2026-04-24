import { useCallback, useEffect, useMemo, useState } from "react";

import { dayIndexForToday, isEnvelope } from "../models/planShape.js";
import {
  generateWeeklyPlan as generateWeeklyPlanApi,
  getCurrentPlan as getCurrentPlanApi,
} from "../services/planService.js";

/**
 * ViewModel for the weekly plan panel.
 *
 * @param {{
 *   userId: string | null,
 *   getCurrentPlan?: typeof getCurrentPlanApi,
 *   generateWeeklyPlan?: typeof generateWeeklyPlanApi,
 * }} params
 */
export function useWeeklyPlanViewModel({
  userId,
  getCurrentPlan = getCurrentPlanApi,
  generateWeeklyPlan = generateWeeklyPlanApi,
}) {
  const [plan, setPlan] = useState(/** @type {any} */ (null));
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [error, setError] = useState(/** @type {string | null} */ (null));

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCurrentPlan();
      setPlan(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load plan.");
    } finally {
      setLoading(false);
    }
  }, [userId, getCurrentPlan]);

  useEffect(() => {
    load();
  }, [load]);

  const weekDayIndex = useMemo(
    () => (plan?.start_date ? dayIndexForToday(plan.start_date) : null),
    [plan]
  );

  const generate = useCallback(async () => {
    if (!userId) return;
    setGenLoading(true);
    setError(null);
    try {
      const data = await generateWeeklyPlan();
      setPlan(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate plan.");
    } finally {
      setGenLoading(false);
    }
  }, [userId, generateWeeklyPlan]);

  const showLegacy = Boolean(plan && Array.isArray(plan.tasks));
  const showEnvelope = Boolean(plan && isEnvelope(plan.tasks));

  return {
    plan,
    setPlan,
    loading,
    genLoading,
    error,
    setError,
    weekDayIndex,
    showLegacy,
    showEnvelope,
    generate,
  };
}

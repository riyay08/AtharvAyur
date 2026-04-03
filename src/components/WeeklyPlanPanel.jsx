import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { DynamicCategoryStack } from "./DynamicCategoryStack";
import { generateWeeklyPlan, getCurrentPlan } from "../api";

/**
 * @param {string} startDateStr - YYYY-MM-DD (Monday)
 */
function dayIndexForToday(startDateStr) {
  const [y, m, d] = startDateStr.split("-").map(Number);
  const start = new Date(y, m - 1, d);
  const today = new Date();
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const diffMs = t0.getTime() - start.getTime();
  const diffDays = Math.round(diffMs / 86400000);
  if (diffDays < 0 || diffDays > 6) return null;
  return diffDays;
}

function isNewPlanEnvelope(tasks) {
  return tasks && typeof tasks === "object" && !Array.isArray(tasks) && Array.isArray(tasks.days);
}

/**
 * @param {{ userId: string | null }} props
 */
export function WeeklyPlanPanel({ userId }) {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCurrentPlan(userId);
      setPlan(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load plan.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const weekDayIndex = useMemo(() => {
    if (!plan?.start_date) return null;
    return dayIndexForToday(plan.start_date);
  }, [plan]);

  const handleGenerate = async () => {
    if (!userId) return;
    setGenLoading(true);
    setError(null);
    try {
      const data = await generateWeeklyPlan(userId);
      setPlan(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate plan.");
    } finally {
      setGenLoading(false);
    }
  };

  const showLegacy = plan && plan.tasks && Array.isArray(plan.tasks);

  return (
    <section
      className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label="Weekly plan"
    >
      <div className="pointer-events-none absolute right-0 top-0 h-32 w-32 rounded-full bg-emerald-500/10 blur-2xl" />

      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-emerald-200/70">
            This week
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-50">Dynamic plan stack</h2>
          {plan?.start_date && (
            <p className="mt-1 flex items-center gap-2 text-sm text-slate-400">
              <CalendarDays className="h-4 w-4 text-amber-200/60" aria-hidden />
              Week of {plan.start_date}
            </p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!userId || genLoading}
            className="inline-flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-100 transition hover:bg-amber-500/20 disabled:opacity-40"
          >
            {genLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {genLoading ? "Generating…" : "Generate plan"}
          </button>
        </div>
      </div>

      {error && (
        <p className="relative mt-4 rounded-xl border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      )}

      <div className="relative mt-6 space-y-3">
        {!userId && (
          <p className="text-sm text-slate-500">Complete onboarding to see your weekly plan.</p>
        )}
        {userId && loading && !plan && (
          <p className="flex items-center gap-2 text-sm text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading plan…
          </p>
        )}
        {userId && !loading && !plan && (
          <p className="text-sm text-slate-400">
            No plan for this week yet. Tap <span className="text-amber-200/90">Generate plan</span> to
            create one from your profile and recent chat themes.
          </p>
        )}
        {userId && plan && showLegacy && (
          <p className="text-sm text-slate-400">
            This plan uses an older format. Tap <span className="text-amber-200/90">Generate plan</span>{" "}
            to upgrade to the new Mind / Fuel / Body stack with context.
          </p>
        )}
        {userId && plan && isNewPlanEnvelope(plan.tasks) && weekDayIndex === null && (
          <p className="mb-4 text-sm text-amber-200/70">
            Today may fall outside the week anchored to this plan&apos;s start date — we&apos;ll still
            match by calendar day when possible.
          </p>
        )}
        {userId && plan && isNewPlanEnvelope(plan.tasks) && (
          <DynamicCategoryStack
            plan={plan}
            userId={userId}
            weekDayIndex={weekDayIndex}
            onPlanUpdated={setPlan}
            onError={(msg) => setError(msg)}
          />
        )}
      </div>
    </section>
  );
}

import { CalendarDays, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { DynamicCategoryStackContainer } from "../containers/DynamicCategoryStackContainer.jsx";

/**
 * Presentational shell for the weekly plan section.
 */
export function WeeklyPlanView({
  userId,
  plan,
  loading,
  genLoading,
  error,
  weekDayIndex,
  showLegacy,
  showEnvelope,
  onGenerate,
  onPlanUpdated,
  onError,
}) {
  const { t } = useTranslation();
  return (
    <section
      className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label={t("plan.title")}
    >
      <div className="pointer-events-none absolute right-0 top-0 h-32 w-32 rounded-full bg-emerald-500/10 blur-2xl" />

      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-emerald-200/70">
            {t("plan.label")}
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-50">{t("plan.title")}</h2>
          {plan?.start_date && (
            <p className="mt-1 flex items-center gap-2 text-sm text-slate-400">
              <CalendarDays className="h-4 w-4 text-amber-200/60" aria-hidden />
              {t("plan.weekOf", { date: plan.start_date })}
            </p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={onGenerate}
            disabled={!userId || genLoading}
            className="inline-flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-100 transition hover:bg-amber-500/20 disabled:opacity-40"
          >
            {genLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {genLoading ? t("plan.generating") : t("plan.generate")}
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
          <p className="text-sm text-slate-500">{t("plan.noUserHint")}</p>
        )}
        {userId && loading && !plan && (
          <p className="flex items-center gap-2 text-sm text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" /> {t("plan.loading")}
          </p>
        )}
        {userId && !loading && !plan && (
          <p className="text-sm text-slate-400">{t("plan.empty")}</p>
        )}
        {userId && showLegacy && (
          <p className="text-sm text-slate-400">{t("plan.legacy")}</p>
        )}
        {userId && showEnvelope && weekDayIndex === null && (
          <p className="mb-4 text-sm text-amber-200/70">{t("plan.outOfRange")}</p>
        )}
        {userId && showEnvelope && (
          <DynamicCategoryStackContainer
            plan={plan}
            userId={userId}
            weekDayIndex={weekDayIndex}
            onPlanUpdated={onPlanUpdated}
            onError={onError}
          />
        )}
      </div>
    </section>
  );
}

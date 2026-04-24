import { ChevronDown, Check, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  allDone,
  countDone,
  firstOpenTask,
  pillarTasks,
} from "../models/planShape.js";

const PILLARS = [
  { key: "Mind", ring: "from-violet-500/25 to-fuchsia-500/10", border: "border-violet-400/20" },
  { key: "Fuel", ring: "from-amber-500/25 to-orange-500/10", border: "border-amber-400/20" },
  { key: "Body", ring: "from-emerald-500/25 to-teal-500/10", border: "border-emerald-400/20" },
];

/**
 * Presentational view for the daily Mind/Fuel/Body stack.
 */
export function DynamicCategoryStackView({
  day,
  focusMessage,
  expanded,
  slideOut,
  greenKey,
  busy,
  onToggleExpand,
  onCompleteTask,
}) {
  const { t } = useTranslation();
  if (!day) {
    return <p className="text-sm text-slate-400">{t("plan.missingDay")}</p>;
  }

  return (
    <div className="space-y-6">
      {focusMessage ? (
        <div className="relative overflow-hidden rounded-2xl border border-amber-400/25 bg-gradient-to-br from-amber-500/15 via-amber-500/5 to-transparent p-5 shadow-[0_0_40px_rgba(251,191,36,0.12)]">
          <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-amber-400/20 blur-2xl" />
          <div className="relative flex gap-3">
            <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-amber-200/90" aria-hidden />
            <div>
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-amber-200/70">
                {t("plan.todaysFocus")}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-100/95">{focusMessage}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="space-y-8">
        {PILLARS.map((meta) => {
          const tasks = pillarTasks(day, meta.key);
          const firstOpen = firstOpenTask(tasks);
          const allDoneForPillar = allDone(tasks);
          const expandKey = firstOpen ? `${meta.key}-${firstOpen.id}` : null;
          const isOpen = expandKey && expanded === expandKey;
          const isSliding =
            slideOut && slideOut.pillar === meta.key && slideOut.taskId === firstOpen?.id;
          const rowKey = firstOpen ? `${meta.key}-${firstOpen.id}` : `${meta.key}-empty`;
          const isCheckboxGreen = greenKey === rowKey;
          const label = t(`plan.pillars.${meta.key}.label`);
          const blurb = t(`plan.pillars.${meta.key}.blurb`);

          if (allDoneForPillar) {
            return (
              <div key={meta.key}>
                <div className="mb-3 flex items-baseline justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold tracking-tight text-slate-100">{label}</h3>
                    <p className="text-xs text-slate-500">{blurb}</p>
                  </div>
                </div>
                <div
                  className={`rounded-2xl border border-emerald-400/35 bg-gradient-to-br ${meta.ring} p-6 text-center`}
                >
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-emerald-400/40 bg-emerald-500/15 text-emerald-200">
                    <Check className="h-6 w-6" strokeWidth={2.5} />
                  </div>
                  <p className="mt-3 text-base font-semibold text-emerald-100">
                    {t("plan.pillarComplete", { pillar: label })}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">{t("plan.pillarCompleteSub")}</p>
                </div>
              </div>
            );
          }

          if (!firstOpen) {
            return (
              <div key={meta.key}>
                <h3 className="text-sm font-semibold text-slate-200">{label}</h3>
                <p className="mt-2 text-sm text-slate-500">{t("plan.noTasksInPillar")}</p>
              </div>
            );
          }

          return (
            <div key={meta.key}>
              <div className="mb-3 flex items-baseline justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold tracking-tight text-slate-100">{label}</h3>
                  <p className="text-xs text-slate-500">{blurb}</p>
                </div>
              </div>

              <div className="relative overflow-hidden rounded-2xl">
                <div
                  key={rowKey}
                  className={`rounded-2xl border bg-black/30 p-4 shadow-lg backdrop-blur-sm ${meta.border} touch-manipulation ${
                    isSliding ? "animate-plan-card-exit" : "animate-plan-card-enter"
                  }`}
                >
                  <div className="flex items-start gap-3 sm:gap-4">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onCompleteTask(meta.key, firstOpen);
                      }}
                      onPointerDown={(e) => e.stopPropagation()}
                      disabled={busy}
                      className={`relative z-20 flex min-h-[48px] min-w-[48px] shrink-0 cursor-pointer select-none items-center justify-center rounded-2xl border-2 transition-all duration-200 ease-out active:scale-90 disabled:pointer-events-none disabled:opacity-40 ${
                        isCheckboxGreen
                          ? "border-emerald-400 bg-emerald-500/45 text-emerald-50 shadow-[0_0_24px_rgba(52,211,153,0.45)] ring-2 ring-emerald-400/30"
                          : "border-white/30 bg-white/5 text-emerald-300/90 hover:border-emerald-400/55 hover:bg-emerald-500/15 hover:shadow-[0_0_18px_rgba(52,211,153,0.2)]"
                      }`}
                      aria-label={t("plan.markComplete")}
                    >
                      <Check
                        className={`h-6 w-6 transition-opacity duration-200 ${
                          isCheckboxGreen ? "opacity-100" : "opacity-30"
                        }`}
                        strokeWidth={2.75}
                        aria-hidden
                      />
                    </button>

                    <button
                      type="button"
                      className="min-w-0 flex-1 touch-manipulation rounded-xl py-1 text-left outline-none ring-offset-2 ring-offset-[#0b0d11] focus-visible:ring-2 focus-visible:ring-amber-400/40"
                      onClick={() => onToggleExpand(meta.key, firstOpen.id)}
                      aria-expanded={Boolean(isOpen)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-[15px] font-medium leading-snug text-slate-50">{firstOpen.task}</p>
                        <ChevronDown
                          className={`mt-0.5 h-5 w-5 shrink-0 text-slate-500 transition-transform duration-300 ${
                            isOpen ? "rotate-180" : ""
                          }`}
                          aria-hidden
                        />
                      </div>

                      <div
                        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
                          isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                        }`}
                      >
                        <div className="overflow-hidden">
                          <p className="mt-3 border-t border-white/10 pt-3 text-sm leading-relaxed text-slate-500">
                            {firstOpen.context_reason}
                          </p>
                        </div>
                      </div>
                    </button>
                  </div>

                  <p className="mt-3 pl-[60px] text-[0.7rem] uppercase tracking-wider text-slate-600 sm:pl-14">
                    {t("plan.doneCounter", {
                      done: countDone(tasks),
                      total: tasks.length,
                      pillar: label,
                    })}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

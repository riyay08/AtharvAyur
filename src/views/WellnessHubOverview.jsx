import { Activity, CalendarRange, ClipboardList, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  checkInIsToday,
  extractDominantDosha,
  todayPlanTaskCounts,
} from "../models/wellnessDashboard.js";
import { useWellnessDashboard } from "../viewmodels/useWellnessDashboard.js";

/**
 * @param {string} ymd
 * @param {string} [lang]
 */
function formatDisplayDate(ymd, lang) {
  if (!ymd) return "";
  const parts = String(ymd).split("-").map(Number);
  if (parts.length < 3 || parts.some((n) => !Number.isFinite(n))) return ymd;
  const [y, m, d] = parts;
  const dt = new Date(y, m - 1, d);
  const loc = lang?.toLowerCase().startsWith("hi") ? "hi-IN" : "en-US";
  return dt.toLocaleDateString(loc, { weekday: "short", month: "short", day: "numeric" });
}

/**
 * @param {Record<string, unknown>} ci
 * @param {(k: string) => string} t
 */
function checkInSummaryLine(ci, t) {
  const sleep = t(`checkin.sleepOptions.${ci.sleep_quality}`);
  const dig = t(`checkin.digestionOptions.${ci.digestion}`);
  const en = t(`checkin.energyOptions.${ci.energy_state}`);
  const mv = t(`checkin.movementOptions.${ci.movement}`);
  const water = t("checkin.glasses", { count: ci.water_glasses });
  return [sleep, dig, en, mv, water].join(" · ");
}

/**
 * Overview landing: live status from GET /profile/me + shortcuts.
 *
 * @param {{ userId?: string | null, onGo: (tab: string) => void }} props
 */
export function WellnessHubOverview({ userId, onGo }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language || "en";
  const { me, loading, error } = useWellnessDashboard(userId);

  const shortcuts = [
    { tab: "checkin", title: t("hub.shortcut.checkinTitle"), blurb: t("hub.shortcut.checkinBlurb") },
    { tab: "environment", title: t("hub.shortcut.tipTitle"), blurb: t("hub.shortcut.tipBlurb") },
    { tab: "plan", title: t("hub.shortcut.planTitle"), blurb: t("hub.shortcut.planBlurb") },
    { tab: "chat", title: t("hub.shortcut.chatTitle"), blurb: t("hub.shortcut.chatBlurb") },
  ];

  const dosha = me?.health_profile ? extractDominantDosha(me.health_profile) : null;
  const doshaLabel = dosha ? t(`quiz.doshaLabels.${dosha}`) : null;

  const latest = me?.latest_checkin ?? null;
  const loggedToday = latest ? checkInIsToday(latest) : false;
  const checkinLine = latest ? checkInSummaryLine(latest, t) : "";

  const plan = me?.active_weekly_plan ?? null;
  const planCounts =
    plan?.tasks && plan?.start_date
      ? todayPlanTaskCounts(plan.tasks, String(plan.start_date))
      : null;
  const weekLabel = plan?.start_date ? formatDisplayDate(String(plan.start_date), lang) : "";

  const planProgressPct =
    planCounts && planCounts.total > 0
      ? Math.round((planCounts.done / planCounts.total) * 100)
      : 0;

  return (
    <div className="space-y-10">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-300/80" aria-hidden />
          <h2 className="text-lg font-semibold text-slate-50 md:text-xl">{t("hub.snapshotTitle")}</h2>
        </div>
        <p className="max-w-2xl text-sm leading-relaxed text-slate-400">{t("hub.snapshotSubtitle")}</p>
      </div>

      {error ? (
        <p
          role="status"
          className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100/90"
        >
          {t("hub.status.loadError")}
        </p>
      ) : null}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-3" aria-busy="true" aria-label={t("hub.status.loading")}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.04]"
            />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          {/* Dosha — read-only snapshot (full edit lives under Update assessment in the header) */}
          <div className="flex flex-col rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.06] to-black/20 p-5">
            <div className="flex items-center gap-2 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
              <Activity className="h-4 w-4 text-emerald-400/80" aria-hidden />
              {t("hub.status.doshaTitle")}
            </div>
            {doshaLabel ? (
              <p className="mt-4 text-lg font-semibold text-slate-50">{doshaLabel}</p>
            ) : (
              <p className="mt-4 text-sm leading-relaxed text-slate-400">{t("hub.status.doshaUnset")}</p>
            )}
            <p className="mt-auto pt-6 text-xs leading-relaxed text-slate-500">{t("hub.status.doshaHint")}</p>
          </div>

          {/* Check-in */}
          <button
            type="button"
            onClick={() => onGo("checkin")}
            className="flex flex-col rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.06] to-black/20 p-5 text-left transition hover:border-emerald-400/25 hover:bg-emerald-500/[0.04]"
          >
            <div className="flex items-center gap-2 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
              <ClipboardList className="h-4 w-4 text-amber-300/80" aria-hidden />
              {t("hub.status.checkinTitle")}
            </div>
            {!latest ? (
              <p className="mt-4 text-sm text-slate-400">{t("hub.status.checkinNone")}</p>
            ) : loggedToday ? (
              <>
                <p className="mt-4 text-lg font-semibold text-emerald-200/95">{t("hub.status.checkinToday")}</p>
                <p className="mt-1 text-xs text-emerald-400/70">{t("hub.status.checkinTodayHint")}</p>
              </>
            ) : (
              <>
                <p className="mt-4 text-sm font-medium text-amber-200/90">{t("hub.status.checkinPending")}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {t("hub.status.checkinLast", {
                    date: formatDisplayDate(String(latest.check_in_date), lang),
                  })}
                </p>
              </>
            )}
            {latest ? (
              <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-slate-500">{checkinLine}</p>
            ) : null}
            <span className="mt-auto pt-4 text-xs font-medium text-emerald-400/90">{t("hub.status.open")}</span>
          </button>

          {/* Plan */}
          <button
            type="button"
            onClick={() => onGo("plan")}
            className="flex flex-col rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.06] to-black/20 p-5 text-left transition hover:border-emerald-400/25 hover:bg-emerald-500/[0.04]"
          >
            <div className="flex items-center gap-2 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
              <CalendarRange className="h-4 w-4 text-teal-300/80" aria-hidden />
              {t("hub.status.planTitle")}
            </div>
            {!plan ? (
              <p className="mt-4 text-sm text-slate-400">{t("hub.status.planEmpty")}</p>
            ) : (
              <>
                <p className="mt-4 text-sm font-medium text-slate-200">
                  {t("hub.status.planWeek", { date: weekLabel })}
                </p>
                {planCounts && planCounts.total > 0 ? (
                  <>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.08]">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-teal-400 transition-[width] duration-500"
                        style={{ width: `${planProgressPct}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs tabular-nums text-slate-400">
                      {t("hub.status.planProgress", {
                        done: planCounts.done,
                        total: planCounts.total,
                      })}
                    </p>
                  </>
                ) : (
                  <p className="mt-4 text-xs text-slate-500">{t("hub.status.planNoTasksToday")}</p>
                )}
              </>
            )}
            <span className="mt-auto pt-4 text-xs font-medium text-emerald-400/90">{t("hub.status.open")}</span>
          </button>
        </div>
      )}

      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">{t("hub.gotoTitle")}</h3>
        <ul className="grid gap-3 sm:grid-cols-2">
          {shortcuts.map(({ tab, title, blurb }) => (
            <li key={tab}>
              <button
                type="button"
                onClick={() => onGo(tab)}
                className="group flex h-full w-full flex-col rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-left transition hover:border-emerald-400/25 hover:bg-emerald-500/[0.06]"
              >
                <span className="text-sm font-semibold text-slate-100 group-hover:text-emerald-100">{title}</span>
                <span className="mt-1.5 text-xs leading-relaxed text-slate-500 group-hover:text-slate-400">
                  {blurb}
                </span>
                <span className="mt-3 text-xs font-medium text-emerald-400/90">{t("hub.openSection")}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

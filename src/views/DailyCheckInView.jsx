import { Check, ChevronDown, Droplets, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  DIGESTION_VALUES,
  ENERGY_ORDER,
  MOVEMENT_VALUES,
} from "../models/checkinModel.js";
import { dayLabel, normalizeYmd } from "../models/checkinModel.js";

const SLEEP_VALUES = ["heavy", "restless", "refreshed"];
const SLEEP_EMOJI = { heavy: "🌙", restless: "🌀", refreshed: "☀️" };
const MAX_WATER_ICONS = 12;

function EnergyStateSlider({ value, onChange }) {
  const { t } = useTranslation();
  const idx = Math.max(0, ENERGY_ORDER.indexOf(value));
  const thumbLeftPct = idx === 0 ? 0 : idx === 1 ? 50 : 100;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/20 px-3 py-4 backdrop-blur-sm">
      <p className="mb-1 text-center text-[0.65rem] font-medium uppercase tracking-[0.2em] text-slate-500">
        {t("checkin.energy")}
      </p>
      <div className="relative mx-1 mt-3 h-12 select-none">
        <div
          className="pointer-events-none absolute left-[6%] right-[6%] top-[22px] h-[3px] rounded-full bg-gradient-to-r from-rose-500/35 via-amber-400/30 to-slate-500/35"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute top-[17px] h-5 w-5 -translate-x-1/2 rounded-full border-2 border-amber-400/55 bg-amber-500/25 shadow-[0_0_22px_rgba(251,191,36,0.22)] transition-[left] duration-200 ease-out"
          style={{ left: `${thumbLeftPct === 0 ? 6 : thumbLeftPct === 50 ? 50 : 94}%` }}
          aria-hidden
        />
        <div className="relative flex h-full items-start justify-between px-[2%]">
          {ENERGY_ORDER.map((v) => {
            const active = value === v;
            const label = t(`checkin.energyOptions.${v}`);
            return (
              <button
                key={v}
                type="button"
                onClick={() => onChange(v)}
                className="group flex w-[30%] max-w-[5.5rem] flex-col items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f1218] rounded-xl py-1"
                aria-pressed={active}
                aria-label={label}
              >
                <span
                  className={`mt-2.5 h-3 w-3 shrink-0 rounded-full border-2 transition-all duration-200 ${
                    active
                      ? "scale-110 border-amber-300/80 bg-amber-400/40 shadow-[0_0_12px_rgba(251,191,36,0.35)]"
                      : "border-white/20 bg-black/40 group-hover:border-white/35"
                  }`}
                />
                <span
                  className={`text-[0.7rem] font-medium leading-tight ${
                    active ? "text-amber-100/95" : "text-slate-500 group-hover:text-slate-400"
                  }`}
                >
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * Presentational view. All behavior lives in `useDailyCheckInViewModel`.
 */
export function DailyCheckInView({
  userId,
  stripDays,
  weekLoading,
  weekError,
  selectedDate,
  todayStr,
  isFormExpanded,
  sleepQuality,
  digestion,
  energyState,
  movement,
  water,
  status,
  message,
  onSelectDay,
  onExpand,
  onSleepChange,
  onDigestionChange,
  onEnergyChange,
  onMovementChange,
  onWaterTap,
  onSubmit,
}) {
  const { t } = useTranslation();
  return (
    <section
      className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label={t("checkin.title")}
    >
      <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-amber-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />

      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-amber-200/80">
            {t("checkin.label")}
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-50">
            {t("checkin.title")}
          </h2>
          <p className="mt-1 text-sm text-slate-400">{t("checkin.subtitle")}</p>
        </div>
        <Sparkles className="h-8 w-8 shrink-0 text-amber-300/60" aria-hidden />
      </div>

      <div className="relative mt-6">
        <p className="mb-3 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
          {t("checkin.lastSevenDays")}
        </p>
        {weekError && <p className="mb-2 text-sm text-rose-300/90">{weekError}</p>}
        <div
          className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:justify-between"
          role="list"
        >
          {!userId ? (
            <p className="text-sm text-slate-500">{t("checkin.noUserHint")}</p>
          ) : weekLoading && !stripDays.length ? (
            <p className="text-sm text-slate-500">{t("checkin.loadingDays")}</p>
          ) : (
            stripDays.map((slot) => {
              const ymd = normalizeYmd(slot.check_in_date);
              const { weekday, dayNum } = dayLabel(ymd);
              const done = Boolean(slot.record);
              const isSelected = ymd === selectedDate;
              const isToday = ymd === todayStr;
              return (
                <button
                  key={ymd}
                  type="button"
                  role="listitem"
                  onClick={() => onSelectDay(ymd)}
                  className={`relative flex min-w-[3.35rem] shrink-0 flex-col items-center rounded-2xl border px-2.5 py-2.5 transition-all duration-300 ${
                    done
                      ? "border-emerald-400/45 bg-emerald-500/12 shadow-[0_0_20px_rgba(52,211,153,0.18)]"
                      : "border-white/10 bg-black/25 hover:border-white/20"
                  } ${isSelected ? "ring-2 ring-amber-400/50 ring-offset-2 ring-offset-[#14181f]" : ""} ${
                    isToday && !isSelected ? "ring-1 ring-white/15" : ""
                  }`}
                >
                  {done && (
                    <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/90 text-[10px] font-bold text-emerald-950 shadow-sm">
                      <Check className="h-2.5 w-2.5" strokeWidth={3} aria-hidden />
                    </span>
                  )}
                  <span className="text-[0.65rem] font-medium uppercase tracking-wide text-slate-500">
                    {weekday}
                  </span>
                  <span className="mt-0.5 text-lg font-semibold tabular-nums text-slate-100">{dayNum}</span>
                </button>
              );
            })
          )}
        </div>
      </div>

      <div
        className={`mt-6 grid transition-[grid-template-rows] duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          isFormExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="min-h-0 overflow-hidden">
          <div
            className={`space-y-5 transition-opacity duration-300 ease-out ${
              isFormExpanded ? "opacity-100" : "pointer-events-none opacity-0"
            }`}
          >
            <p className="text-xs text-slate-500">
              {t("checkin.editing")}{" "}
              <span className="font-medium text-slate-300">
                {selectedDate === todayStr ? t("checkin.today") : selectedDate}
              </span>
            </p>

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                {t("checkin.sleep")}
              </p>
              <div className="flex flex-wrap gap-2">
                {SLEEP_VALUES.map((value) => {
                  const active = sleepQuality === value;
                  const label = t(`checkin.sleepOptions.${value}`);
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onSleepChange(value)}
                      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-amber-400/50 bg-amber-500/15 text-amber-50 shadow-[0_0_24px_rgba(251,191,36,0.12)]"
                          : "border-white/10 bg-black/25 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                      aria-label={`${t("checkin.sleep")} ${label}`}
                    >
                      <span className="text-lg leading-none" role="img" aria-hidden>
                        {SLEEP_EMOJI[value]}
                      </span>
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                {t("checkin.digestion")}
              </p>
              <div className="flex flex-wrap gap-2">
                {DIGESTION_VALUES.map((value) => {
                  const active = digestion === value;
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onDigestionChange(value)}
                      className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-emerald-400/45 bg-emerald-500/15 text-emerald-100"
                          : "border-white/10 bg-black/20 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                    >
                      {t(`checkin.digestionOptions.${value}`)}
                    </button>
                  );
                })}
              </div>
            </div>

            <EnergyStateSlider value={energyState} onChange={onEnergyChange} />

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                {t("checkin.movement")}
              </p>
              <div className="flex flex-wrap gap-2">
                {MOVEMENT_VALUES.map((value) => {
                  const active = movement === value;
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onMovementChange(value)}
                      className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-sky-400/40 bg-sky-500/15 text-sky-100"
                          : "border-white/10 bg-black/20 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                    >
                      {t(`checkin.movementOptions.${value}`)}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  {t("checkin.hydration")}
                </p>
                <span className="text-sm font-semibold text-emerald-200/90">
                  {t("checkin.glasses", { count: water })}
                </span>
              </div>
              <div className="flex flex-wrap gap-2" role="group" aria-label={t("checkin.hydration")}>
                {Array.from({ length: MAX_WATER_ICONS }, (_, i) => {
                  const filled = i < water;
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => onWaterTap(i)}
                      className={`flex h-11 w-11 items-center justify-center rounded-xl border transition ${
                        filled
                          ? "border-emerald-400/40 bg-emerald-500/20 text-emerald-200"
                          : "border-white/10 bg-black/25 text-slate-500 hover:border-white/25"
                      }`}
                      aria-label={t("checkin.glassLabel", { n: i + 1 })}
                    >
                      <Droplets className={`h-5 w-5 ${filled ? "fill-current" : ""}`} strokeWidth={1.75} />
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                disabled={!userId || status === "loading"}
                onClick={onSubmit}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-amber-500/90 to-amber-600/90 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-900/30 transition hover:from-amber-400 hover:to-amber-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {status === "loading" ? (
                  t("checkin.saving")
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    {t("checkin.logCheckin")}
                  </>
                )}
              </button>
              {message && (
                <p
                  className={`text-sm ${status === "error" ? "text-rose-300" : "text-emerald-300/90"}`}
                  role="status"
                >
                  {message}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {!isFormExpanded && userId && (
        <button
          type="button"
          onClick={onExpand}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-black/20 py-3 text-sm font-medium text-slate-300 transition hover:border-emerald-400/30 hover:bg-emerald-500/5 hover:text-slate-100"
        >
          <ChevronDown className="h-4 w-4" aria-hidden />
          {t("checkin.showForm")}
        </button>
      )}
    </section>
  );
}

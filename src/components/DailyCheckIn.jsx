import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, Droplets, Sparkles } from "lucide-react";
import { getCheckInWeek, postCheckIn } from "../api";

const SLEEP_OPTIONS = [
  { value: "heavy", emoji: "🌙", label: "Heavy" },
  { value: "restless", emoji: "🌀", label: "Restless" },
  { value: "refreshed", emoji: "☀️", label: "Refreshed" },
];

const DIGESTION_OPTIONS = [
  { value: "bloated", label: "Bloated" },
  { value: "acidic", label: "Acidic" },
  { value: "calm", label: "Calm" },
];

/** Left → right: Wired, Grounded, Sluggish */
const ENERGY_ORDER = ["wired", "grounded", "sluggish"];
const ENERGY_LABELS = { wired: "Wired", grounded: "Grounded", sluggish: "Sluggish" };

const MOVEMENT_OPTIONS = [
  { value: "rest", label: "Rest" },
  { value: "light", label: "Light" },
  { value: "sweat", label: "Sweat" },
];

const MAX_WATER_ICONS = 12;

/** @returns {string} YYYY-MM-DD in local calendar */
function localYmd(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Normalize API date string to YYYY-MM-DD */
function normYmd(iso) {
  if (iso == null) return "";
  const s = String(iso);
  return s.length >= 10 ? s.slice(0, 10) : s;
}

function dayLabel(ymd) {
  const [y, m, d] = ymd.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return {
    weekday: dt.toLocaleDateString(undefined, { weekday: "short" }),
    dayNum: d,
  };
}

function defaultForm() {
  return {
    sleepQuality: "refreshed",
    digestion: "calm",
    energyState: "grounded",
    movement: "light",
    water: 0,
  };
}

/**
 * Three-stop energy control: Wired (left) · Grounded (center) · Sluggish (right).
 */
function EnergyStateSlider({ value, onChange }) {
  const idx = Math.max(0, ENERGY_ORDER.indexOf(value));
  const thumbLeftPct = idx === 0 ? 0 : idx === 1 ? 50 : 100;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/20 px-3 py-4 backdrop-blur-sm">
      <p className="mb-1 text-center text-[0.65rem] font-medium uppercase tracking-[0.2em] text-slate-500">
        Energy state
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
            return (
              <button
                key={v}
                type="button"
                onClick={() => onChange(v)}
                className="group flex w-[30%] max-w-[5.5rem] flex-col items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f1218] rounded-xl py-1"
                aria-pressed={active}
                aria-label={ENERGY_LABELS[v]}
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
                  {ENERGY_LABELS[v]}
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
 * 7-day strip + collapsible check-in form (upsert any day).
 * @param {{ userId: string | null }} props
 */
export function DailyCheckIn({ userId }) {
  const [weekData, setWeekData] = useState(null);
  const [weekLoading, setWeekLoading] = useState(false);
  const [weekError, setWeekError] = useState(null);

  const [selectedDate, setSelectedDate] = useState(() => localYmd());
  const [isFormExpanded, setIsFormExpanded] = useState(true);
  const [expandInitialized, setExpandInitialized] = useState(false);

  const d0 = defaultForm();
  const [sleepQuality, setSleepQuality] = useState(d0.sleepQuality);
  const [digestion, setDigestion] = useState(d0.digestion);
  const [energyState, setEnergyState] = useState(d0.energyState);
  const [movement, setMovement] = useState(d0.movement);
  const [water, setWater] = useState(d0.water);

  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState(null);

  const todayStr = useMemo(() => localYmd(), []);

  const applyRecord = useCallback((rec) => {
    if (rec && typeof rec === "object") {
      const sq = rec.sleep_quality;
      const dg = rec.digestion;
      const es = rec.energy_state;
      const mv = rec.movement;
      setSleepQuality(typeof sq === "string" && SLEEP_OPTIONS.some((o) => o.value === sq) ? sq : "refreshed");
      setDigestion(typeof dg === "string" && DIGESTION_OPTIONS.some((o) => o.value === dg) ? dg : "calm");
      setEnergyState(typeof es === "string" && ENERGY_ORDER.includes(es) ? es : "grounded");
      setMovement(typeof mv === "string" && MOVEMENT_OPTIONS.some((o) => o.value === mv) ? mv : "light");
      setWater(typeof rec.water_glasses === "number" ? rec.water_glasses : 0);
    } else {
      const d = defaultForm();
      setSleepQuality(d.sleepQuality);
      setDigestion(d.digestion);
      setEnergyState(d.energyState);
      setMovement(d.movement);
      setWater(d.water);
    }
  }, []);

  const loadWeek = useCallback(async () => {
    if (!userId) {
      setWeekData(null);
      return;
    }
    setWeekLoading(true);
    setWeekError(null);
    try {
      const data = await getCheckInWeek(userId, localYmd());
      setWeekData(data);
    } catch (e) {
      setWeekError(e instanceof Error ? e.message : "Could not load check-ins.");
      setWeekData(null);
    } finally {
      setWeekLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    setExpandInitialized(false);
  }, [userId]);

  useEffect(() => {
    loadWeek();
  }, [loadWeek]);

  useEffect(() => {
    if (!weekData?.days || expandInitialized) return;
    const t = localYmd();
    setSelectedDate(t);
    const slot = weekData.days.find((s) => normYmd(s.check_in_date) === t);
    setIsFormExpanded(!slot?.record);
    applyRecord(slot?.record ?? null);
    setExpandInitialized(true);
  }, [weekData, expandInitialized, applyRecord]);

  useEffect(() => {
    if (!weekData?.days) return;
    const slot = weekData.days.find((s) => normYmd(s.check_in_date) === selectedDate);
    applyRecord(slot?.record ?? null);
  }, [selectedDate, weekData, applyRecord]);

  const handleSelectDay = (ymd) => {
    setSelectedDate(ymd);
    setIsFormExpanded(true);
    setMessage(null);
  };

  const handleWaterTap = (index) => {
    setWater(index + 1);
  };

  const submit = async () => {
    if (!userId) return;
    setStatus("loading");
    setMessage(null);
    try {
      const saved = await postCheckIn(userId, {
        check_in_date: selectedDate,
        sleep_quality: sleepQuality,
        digestion,
        energy_state: energyState,
        movement,
        water_glasses: water,
      });
      const refreshed = await getCheckInWeek(userId, localYmd());
      setWeekData(refreshed);
      const ymd = normYmd(saved.check_in_date) || selectedDate;
      setSelectedDate(ymd);
      applyRecord(saved);
      setIsFormExpanded(false);
      setStatus("idle");
      setMessage("Saved.");
      setTimeout(() => setMessage(null), 2200);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not save check-in.");
    }
  };

  const stripDays = weekData?.days ?? [];

  return (
    <section
      className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label="Daily check-in"
    >
      <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-amber-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />

      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-amber-200/80">
            Daily ritual
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-50">Quick check-in</h2>
          <p className="mt-1 text-sm text-slate-400">Under 15 seconds — tap a day, tap your state, done.</p>
        </div>
        <Sparkles className="h-8 w-8 shrink-0 text-amber-300/60" aria-hidden />
      </div>

      {/* 7-day strip */}
      <div className="relative mt-6">
        <p className="mb-3 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
          Last 7 days
        </p>
        {weekError && <p className="mb-2 text-sm text-rose-300/90">{weekError}</p>}
        <div
          className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:justify-between"
          role="list"
        >
          {!userId ? (
            <p className="text-sm text-slate-500">Complete onboarding to track check-ins.</p>
          ) : weekLoading && !stripDays.length ? (
            <p className="text-sm text-slate-500">Loading days…</p>
          ) : (
            stripDays.map((slot) => {
              const ymd = normYmd(slot.check_in_date);
              const { weekday, dayNum } = dayLabel(ymd);
              const done = Boolean(slot.record);
              const isSelected = ymd === selectedDate;
              const isToday = ymd === todayStr;
              return (
                <button
                  key={ymd}
                  type="button"
                  role="listitem"
                  onClick={() => handleSelectDay(ymd)}
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

      {/* Collapsible form */}
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
              Editing{" "}
              <span className="font-medium text-slate-300">
                {selectedDate === todayStr ? "today" : selectedDate}
              </span>
            </p>

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">Sleep</p>
              <div className="flex flex-wrap gap-2">
                {SLEEP_OPTIONS.map((opt) => {
                  const active = sleepQuality === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setSleepQuality(opt.value)}
                      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-amber-400/50 bg-amber-500/15 text-amber-50 shadow-[0_0_24px_rgba(251,191,36,0.12)]"
                          : "border-white/10 bg-black/25 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                      aria-label={`Sleep ${opt.label}`}
                    >
                      <span className="text-lg leading-none" role="img" aria-hidden>
                        {opt.emoji}
                      </span>
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">Digestion</p>
              <div className="flex flex-wrap gap-2">
                {DIGESTION_OPTIONS.map((opt) => {
                  const active = digestion === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setDigestion(opt.value)}
                      className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-emerald-400/45 bg-emerald-500/15 text-emerald-100"
                          : "border-white/10 bg-black/20 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <EnergyStateSlider value={energyState} onChange={setEnergyState} />

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">Movement</p>
              <div className="flex flex-wrap gap-2">
                {MOVEMENT_OPTIONS.map((opt) => {
                  const active = movement === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setMovement(opt.value)}
                      className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                        active
                          ? "border-sky-400/40 bg-sky-500/15 text-sky-100"
                          : "border-white/10 bg-black/20 text-slate-300 hover:border-white/20"
                      }`}
                      aria-pressed={active}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Hydration</p>
                <span className="text-sm font-semibold text-emerald-200/90">{water} glasses</span>
              </div>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Water glasses">
                {Array.from({ length: MAX_WATER_ICONS }, (_, i) => {
                  const filled = i < water;
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleWaterTap(i)}
                      className={`flex h-11 w-11 items-center justify-center rounded-xl border transition ${
                        filled
                          ? "border-emerald-400/40 bg-emerald-500/20 text-emerald-200"
                          : "border-white/10 bg-black/25 text-slate-500 hover:border-white/25"
                      }`}
                      aria-label={`Glass ${i + 1}`}
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
                onClick={submit}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-amber-500/90 to-amber-600/90 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-900/30 transition hover:from-amber-400 hover:to-amber-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {status === "loading" ? (
                  "Saving…"
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    Log check-in
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
          onClick={() => setIsFormExpanded(true)}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-black/20 py-3 text-sm font-medium text-slate-300 transition hover:border-emerald-400/30 hover:bg-emerald-500/5 hover:text-slate-100"
        >
          <ChevronDown className="h-4 w-4" aria-hidden />
          Show check-in form
        </button>
      )}
    </section>
  );
}

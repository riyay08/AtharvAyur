import { useCallback, useMemo, useState } from "react";
import { ChevronDown, Check, Sparkles } from "lucide-react";
import { putPlanTask } from "../api";

const PILLARS = [
  {
    key: "Mind",
    label: "Mind",
    blurb: "Nervous system & focus",
    ring: "from-violet-500/25 to-fuchsia-500/10",
    border: "border-violet-400/20",
  },
  {
    key: "Fuel",
    label: "Fuel",
    blurb: "Nourishment & digestion",
    ring: "from-amber-500/25 to-orange-500/10",
    border: "border-amber-400/20",
  },
  {
    key: "Body",
    label: "Body",
    blurb: "Movement & recovery",
    ring: "from-emerald-500/25 to-teal-500/10",
    border: "border-emerald-400/20",
  },
];

function todayYmd() {
  const t = new Date();
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, "0");
  const d = String(t.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function resolveTodayDay(envelope, fallbackIndex) {
  const days = envelope?.days;
  if (!Array.isArray(days) || !days.length) return { day: null, dayIndex: null };
  const tstr = todayYmd();
  const idx = days.findIndex((x) => x && x.date === tstr);
  if (idx >= 0) return { day: days[idx], dayIndex: idx };
  if (fallbackIndex != null && days[fallbackIndex]) {
    return { day: days[fallbackIndex], dayIndex: fallbackIndex };
  }
  return { day: null, dayIndex: null };
}

function pillarTasks(day, pillarKey) {
  const p = day?.pillars;
  if (!p || typeof p !== "object") return [];
  if (Array.isArray(p[pillarKey])) return p[pillarKey];
  const want = pillarKey.toLowerCase();
  for (const k of Object.keys(p)) {
    if (typeof k === "string" && k.toLowerCase() === want && Array.isArray(p[k])) return p[k];
  }
  return [];
}

/**
 * Dynamic pillar stack: first uncompleted task per pillar, expandable context, complete + slide.
 * @param {{
 *   plan: { id: string, tasks: { daily_focus_message?: string, days?: unknown[] } },
 *   userId: string,
 *   weekDayIndex: number | null,
 *   onPlanUpdated: (p: object) => void,
 *   onError: (msg: string) => void,
 * }} props
 */
export function DynamicCategoryStack({ plan, userId, weekDayIndex, onPlanUpdated, onError }) {
  const envelope = plan?.tasks && typeof plan.tasks === "object" && !Array.isArray(plan.tasks) ? plan.tasks : null;

  const { day, dayIndex } = useMemo(
    () => resolveTodayDay(envelope, weekDayIndex),
    [envelope, weekDayIndex]
  );

  const [expanded, setExpanded] = useState(null);
  const [slideOut, setSlideOut] = useState(null);
  const [greenKey, setGreenKey] = useState(null);
  const [busy, setBusy] = useState(false);

  const focusMessage = typeof envelope?.daily_focus_message === "string" ? envelope.daily_focus_message : "";

  const toggleExpand = useCallback((pillarKey, taskId) => {
    const key = `${pillarKey}-${taskId}`;
    setExpanded((prev) => (prev === key ? null : key));
  }, []);

  const completeTask = useCallback(
    async (pillarKey, task) => {
      if (!userId || dayIndex == null || busy) return;
      const k = `${pillarKey}-${task.id}`;
      setGreenKey(k);
      setSlideOut({ pillar: pillarKey, taskId: task.id });
      await new Promise((r) => setTimeout(r, 420));
      try {
        setBusy(true);
        const updated = await putPlanTask({
          user_id: userId,
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
    [userId, dayIndex, busy, plan?.id, onPlanUpdated, onError]
  );

  if (!envelope || !day) {
    return (
      <p className="text-sm text-slate-400">
        Plan data is missing today&apos;s section. Try refreshing or generating a new plan.
      </p>
    );
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
                Today&apos;s focus
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-100/95">{focusMessage}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="space-y-8">
        {PILLARS.map((meta) => {
          const tasks = pillarTasks(day, meta.key);
          const firstOpen = tasks.find((t) => !t.completed);
          const allDone = tasks.length > 0 && tasks.every((t) => t.completed);
          const expandKey = firstOpen ? `${meta.key}-${firstOpen.id}` : null;
          const isOpen = expandKey && expanded === expandKey;
          const isSliding =
            slideOut && slideOut.pillar === meta.key && slideOut.taskId === firstOpen?.id;
          const rowKey = `${meta.key}-${firstOpen.id}`;
          const isCheckboxGreen = greenKey === rowKey;

          if (allDone) {
            return (
              <div key={meta.key}>
                <div className="mb-3 flex items-baseline justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold tracking-tight text-slate-100">{meta.label}</h3>
                    <p className="text-xs text-slate-500">{meta.blurb}</p>
                  </div>
                </div>
                <div
                  className={`rounded-2xl border border-emerald-400/35 bg-gradient-to-br ${meta.ring} p-6 text-center`}
                >
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-emerald-400/40 bg-emerald-500/15 text-emerald-200">
                    <Check className="h-6 w-6" strokeWidth={2.5} />
                  </div>
                  <p className="mt-3 text-base font-semibold text-emerald-100">{meta.label} pillar complete</p>
                  <p className="mt-1 text-sm text-slate-400">Beautiful rhythm — carry this momentum forward.</p>
                </div>
              </div>
            );
          }

          if (!firstOpen) {
            return (
              <div key={meta.key}>
                <h3 className="text-sm font-semibold text-slate-200">{meta.label}</h3>
                <p className="mt-2 text-sm text-slate-500">No tasks in this pillar for today.</p>
              </div>
            );
          }

          return (
            <div key={meta.key}>
              <div className="mb-3 flex items-baseline justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold tracking-tight text-slate-100">{meta.label}</h3>
                  <p className="text-xs text-slate-500">{meta.blurb}</p>
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
                        completeTask(meta.key, firstOpen);
                      }}
                      onPointerDown={(e) => e.stopPropagation()}
                      disabled={busy}
                      className={`relative z-20 flex min-h-[48px] min-w-[48px] shrink-0 cursor-pointer select-none items-center justify-center rounded-2xl border-2 transition-all duration-200 ease-out active:scale-90 disabled:pointer-events-none disabled:opacity-40 ${
                        isCheckboxGreen
                          ? "border-emerald-400 bg-emerald-500/45 text-emerald-50 shadow-[0_0_24px_rgba(52,211,153,0.45)] ring-2 ring-emerald-400/30"
                          : "border-white/30 bg-white/5 text-emerald-300/90 hover:border-emerald-400/55 hover:bg-emerald-500/15 hover:shadow-[0_0_18px_rgba(52,211,153,0.2)]"
                      }`}
                      aria-label="Mark complete"
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
                      onClick={() => toggleExpand(meta.key, firstOpen.id)}
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
                    {tasks.filter((t) => t.completed).length}/{tasks.length} done in {meta.label}
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

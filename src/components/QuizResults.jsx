import { Loader2, Sparkles } from "lucide-react";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { DOSHA_LABELS, DOSHA_SUMMARIES } from "../data/quizData";

/**
 * @param {{
 *  scores: { vata: number; pitta: number; kapha: number };
 *  dominantDosha: "vata" | "pitta" | "kapha";
 *  onContinue: () => void;
 *  continuing: boolean;
 *  continueError: string | null;
 * }} props
 */
export function QuizResults({ scores, dominantDosha, onContinue, continuing, continueError }) {
  const chartData = [
    { name: "Vata", score: scores.vata },
    { name: "Pitta", score: scores.pitta },
    { name: "Kapha", score: scores.kapha },
  ];

  const ringTone =
    dominantDosha === "vata"
      ? "from-cyan-500/25 to-sky-500/15 text-cyan-200 border-cyan-400/30"
      : dominantDosha === "pitta"
        ? "from-amber-500/25 to-orange-500/15 text-amber-200 border-amber-400/30"
        : "from-emerald-500/30 to-teal-500/15 text-emerald-200 border-emerald-400/35";

  return (
    <section className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-2xl border border-white/[0.08] bg-black/25 p-5 shadow-inner backdrop-blur-sm md:p-6">
          <p className="text-xs uppercase tracking-[0.18em] text-emerald-400/70">Dosha distribution</p>
          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="rgba(148, 163, 184, 0.25)" />
                <PolarAngleAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Radar
                  name="Distribution"
                  dataKey="score"
                  stroke="#34d399"
                  fill="#34d399"
                  fillOpacity={0.22}
                  isAnimationActive
                  animationDuration={900}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(52, 211, 153, 0.25)",
                    borderRadius: "12px",
                    color: "#e2e8f0",
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="rounded-2xl border border-white/[0.08] bg-black/25 p-5 shadow-inner backdrop-blur-sm md:p-6">
          <p className="text-xs uppercase tracking-[0.18em] text-emerald-400/70">Your dominant dosha</p>
          <div className="mt-4 flex items-center gap-3">
            <div
              className={`rounded-full border bg-gradient-to-br p-3 shadow-[0_0_24px_rgba(52,211,153,0.12)] ${ringTone}`}
            >
              <Sparkles size={20} />
            </div>
            <h2 className="text-2xl font-semibold text-slate-50">{DOSHA_LABELS[dominantDosha]}</h2>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-slate-300 md:text-base">
            {DOSHA_SUMMARIES[dominantDosha]}
          </p>
          <p className="mt-3 text-sm text-slate-500">
            This profile will now personalize your in-app guidance and conversational context.
          </p>

          <button
            type="button"
            onClick={onContinue}
            disabled={continuing}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500/90 to-amber-600/90 px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-900/25 transition hover:from-amber-400 hover:to-amber-500 disabled:opacity-60"
          >
            {continuing ? <Loader2 size={16} className="animate-spin" /> : null}
            Continue to my plan
          </button>
          {continueError ? (
            <p className="mt-3 rounded-xl border border-rose-500/30 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
              {continueError}
            </p>
          ) : null}
        </article>
      </div>
    </section>
  );
}

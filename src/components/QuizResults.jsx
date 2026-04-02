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
      ? "from-cyan-100 to-sky-100 text-cyan-700"
      : dominantDosha === "pitta"
        ? "from-orange-100 to-amber-100 text-orange-700"
        : "from-green-100 to-emerald-100 text-green-700";

  return (
    <section className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-2xl border border-slate-200/80 bg-white p-5 md:p-6">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Dosha distribution</p>
          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="#cbd5e1" />
                <PolarAngleAxis dataKey="name" tick={{ fill: "#334155", fontSize: 12 }} />
                <Radar
                  name="Distribution"
                  dataKey="score"
                  stroke="#0f172a"
                  fill="#475569"
                  fillOpacity={0.24}
                  isAnimationActive
                  animationDuration={900}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200/80 bg-white p-5 md:p-6">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Your dominant dosha</p>
          <div className="mt-4 flex items-center gap-3">
            <div className={`rounded-full bg-gradient-to-br p-3 ${ringTone}`}>
              <Sparkles size={20} />
            </div>
            <h2 className="text-2xl font-semibold text-slate-900">{DOSHA_LABELS[dominantDosha]}</h2>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-slate-700 md:text-base">
            {DOSHA_SUMMARIES[dominantDosha]}
          </p>
          <p className="mt-3 text-sm text-slate-600">
            This profile will now personalize your in-app guidance and conversational context.
          </p>

          <button
            type="button"
            onClick={onContinue}
            disabled={continuing}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            {continuing ? <Loader2 size={16} className="animate-spin" /> : null}
            Continue to my plan
          </button>
          {continueError ? (
            <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {continueError}
            </p>
          ) : null}
        </article>
      </div>
    </section>
  );
}

import { Loader2, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

function DoshaScorePill({ label, score, tone }) {
  return (
    <div
      className={`rounded-2xl border px-3 py-3 text-center ${tone}`}
      role="presentation"
    >
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] opacity-90">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{score}</p>
    </div>
  );
}

/**
 * Pure presentational view for the quiz results + continue CTA.
 *
 * @param {{
 *   scores: { vata: number, pitta: number, kapha: number },
 *   dominantDosha: 'vata' | 'pitta' | 'kapha',
 *   onContinue: () => void,
 *   continuing: boolean,
 *   continueError: string | null,
 * }} props
 */
export function QuizResultsView({ scores, dominantDosha, onContinue, continuing, continueError }) {
  const { t } = useTranslation();

  const chartData = [
    { name: t("quiz.doshaLabels.vata"), score: scores.vata },
    { name: t("quiz.doshaLabels.pitta"), score: scores.pitta },
    { name: t("quiz.doshaLabels.kapha"), score: scores.kapha },
  ];

  const ringTone =
    dominantDosha === "vata"
      ? "from-cyan-500/25 to-sky-500/15 text-cyan-200 border-cyan-400/30"
      : dominantDosha === "pitta"
        ? "from-amber-500/25 to-orange-500/15 text-amber-200 border-amber-400/30"
        : "from-emerald-500/30 to-teal-500/15 text-emerald-200 border-emerald-400/35";

  return (
    <section className="space-y-8">
      <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
        <article className="rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.05] to-black/25 p-6 shadow-panel-soft backdrop-blur-sm md:p-7">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-emerald-300/75">
            {t("quiz.distributionTitle")}
          </p>
          <div className="mt-5 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="rgba(148, 163, 184, 0.25)" />
                <PolarAngleAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Radar
                  name={t("quiz.distributionTitle")}
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

        <article className="flex flex-col rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.05] to-black/25 p-6 shadow-panel-soft backdrop-blur-sm md:p-7">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-emerald-300/75">
            {t("quiz.dominantTitle")}
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-4">
            <div
              className={`rounded-2xl border bg-gradient-to-br p-3.5 shadow-[0_0_28px_rgba(52,211,153,0.1)] ${ringTone}`}
            >
              <Sparkles size={22} aria-hidden />
            </div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-50 md:text-[1.65rem]">
              {t(`quiz.doshaLabels.${dominantDosha}`)}
            </h2>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-2 sm:gap-3">
            <DoshaScorePill
              label={t("quiz.doshaLabels.vata")}
              score={scores.vata}
              tone="border-cyan-400/25 bg-cyan-500/10 text-cyan-100"
            />
            <DoshaScorePill
              label={t("quiz.doshaLabels.pitta")}
              score={scores.pitta}
              tone="border-amber-400/25 bg-amber-500/10 text-amber-100"
            />
            <DoshaScorePill
              label={t("quiz.doshaLabels.kapha")}
              score={scores.kapha}
              tone="border-emerald-400/25 bg-emerald-500/10 text-emerald-100"
            />
          </div>

          <p className="mt-6 max-w-measure text-sm leading-relaxed text-slate-300 md:text-base">
            {t(`quiz.doshaSummaries.${dominantDosha}`)}
          </p>
          <p className="mt-4 text-sm text-slate-500">{t("quiz.personalizationNote")}</p>

          <div className="mt-auto pt-8">
            <button
              type="button"
              onClick={onContinue}
              disabled={continuing}
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-400 to-amber-500 px-4 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-950/25 transition hover:from-amber-300 hover:to-amber-400 disabled:opacity-60"
            >
              {continuing ? <Loader2 size={16} className="animate-spin" aria-hidden /> : null}
              {t("quiz.continueToPlan")}
            </button>
            {continueError ? (
              <p
                role="alert"
                className="mt-3 rounded-xl border border-rose-500/30 bg-rose-950/40 px-3 py-2.5 text-sm text-rose-200"
              >
                {continueError}
              </p>
            ) : null}
          </div>
        </article>
      </div>
    </section>
  );
}


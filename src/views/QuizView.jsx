import { ChevronLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

const KEY_STYLES = {
  a: {
    idle: "border-white/[0.08] bg-white/[0.02] text-slate-300 group-hover:border-vata/35 group-hover:bg-vata/[0.06]",
    active:
      "border-vata/55 bg-vata/15 text-slate-50 shadow-[0_0_0_1px_rgba(126,200,227,0.35),0_12px_40px_rgba(126,200,227,0.12)]",
    badgeIdle: "border-white/15 bg-black/30 text-slate-400",
    badgeActive: "border-vata/50 bg-vata/25 text-cyan-50",
  },
  b: {
    idle: "border-white/[0.08] bg-white/[0.02] text-slate-300 group-hover:border-pitta/35 group-hover:bg-pitta/[0.06]",
    active:
      "border-pitta/55 bg-pitta/15 text-slate-50 shadow-[0_0_0_1px_rgba(217,140,107,0.35),0_12px_40px_rgba(217,140,107,0.12)]",
    badgeIdle: "border-white/15 bg-black/30 text-slate-400",
    badgeActive: "border-pitta/50 bg-pitta/25 text-orange-50",
  },
  c: {
    idle: "border-white/[0.08] bg-white/[0.02] text-slate-300 group-hover:border-kapha/35 group-hover:bg-kapha/[0.06]",
    active:
      "border-kapha/55 bg-kapha/15 text-slate-50 shadow-[0_0_0_1px_rgba(143,175,122,0.35),0_12px_40px_rgba(143,175,122,0.12)]",
    badgeIdle: "border-white/15 bg-black/30 text-slate-400",
    badgeActive: "border-kapha/50 bg-kapha/25 text-emerald-50",
  },
};

function keyStyle(key) {
  const k = String(key).toLowerCase();
  return KEY_STYLES[k] ?? KEY_STYLES.a;
}

/**
 * Pure presentational view for one quiz question + nav. All state is owned by
 * the ViewModel; this component just renders props. Question text/options are
 * already localized by the container before being passed in.
 *
 * Layout follows common assessment UX: constrained reading width (~65ch),
 * explicit option keys (A/B/C), and a sticky footer on small screens so primary
 * navigation stays reachable (NN/g: visibility of system status; WCAG 2.5.5
 * target size for touch).
 *
 * @param {{
 *   question: { id: string, section: string, prompt: string, options: Record<string,string> },
 *   questionIndex: number,
 *   totalQuestions: number,
 *   selectedKey: string | undefined,
 *   progress: number,
 *   onSelectAnswer: (key: string) => void,
 *   onBack: () => void,
 *   onSkipQuestion?: () => void,
 * }} props
 */
export function QuizView({
  question,
  questionIndex,
  totalQuestions,
  selectedKey,
  progress,
  onSelectAnswer,
  onBack,
  onSkipQuestion,
}) {
  const { t } = useTranslation();

  return (
    <div className="space-y-8">
      <section aria-label={t("quiz.progress")} className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-emerald-300/75">
              {question.section}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              {t("quiz.questionLabel", {
                current: questionIndex + 1,
                total: totalQuestions,
              })}
            </p>
          </div>
          <span className="tabular-nums text-sm font-medium text-emerald-200/90">{progress}%</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.07]">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-700 via-teal-500 to-emerald-400 transition-[width] duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </section>

      <section className="rounded-2xl border border-white/[0.07] bg-gradient-to-b from-white/[0.05] to-black/20 p-6 shadow-panel-soft backdrop-blur-sm md:p-8">
        <h2 className="max-w-measure text-lg font-medium leading-snug tracking-tight text-slate-50 md:text-xl">
          <span className="mr-2 font-semibold text-emerald-200/80">{questionIndex + 1}.</span>
          {question.prompt}
        </h2>

        <div className="mt-8 grid gap-3">
          {Object.entries(question.options).map(([key, text]) => {
            const active = selectedKey === key;
            const tone = keyStyle(key);
            const letter = String(key).toUpperCase();

            return (
              <button
                key={key}
                type="button"
                onClick={() => onSelectAnswer(key)}
                className={`group flex w-full gap-4 rounded-2xl border p-4 text-left transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400/50 md:min-h-[3.25rem] md:p-5 ${
                  active ? `${tone.active} scale-[1.01]` : `${tone.idle} hover:-translate-y-px`
                }`}
              >
                <span
                  className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border text-sm font-bold tabular-nums transition-colors ${
                    active ? tone.badgeActive : tone.badgeIdle
                  }`}
                >
                  {letter}
                </span>
                <span className="min-w-0 flex-1 pt-0.5 text-sm leading-relaxed text-slate-200 md:text-[0.9375rem]">
                  {text}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <div className="sticky bottom-0 z-10 -mx-1 border-t border-white/[0.06] bg-gradient-to-t from-[#0b0d11] via-[#0b0d11]/95 to-transparent pb-1 pt-4 md:static md:mx-0 md:border-0 md:bg-transparent md:p-0">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onBack}
            disabled={questionIndex === 0}
            className="inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-white/12 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-white/20 hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-35"
          >
            <ChevronLeft size={16} aria-hidden /> {t("common.back")}
          </button>

          <div className="flex flex-wrap items-center justify-end gap-2">
            {onSkipQuestion ? (
              <button
                type="button"
                onClick={onSkipQuestion}
                className="min-h-[44px] rounded-xl px-3 py-2.5 text-sm font-medium text-slate-500 transition hover:text-slate-300"
              >
                {t("quiz.skipQuestion")}
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

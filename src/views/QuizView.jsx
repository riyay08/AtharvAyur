import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * Pure presentational view for one quiz question + nav. All state is owned by
 * the ViewModel; this component just renders props. Question text/options are
 * already localized by the container before being passed in.
 *
 * @param {{
 *   question: { id: string, section: string, prompt: string, options: Record<string,string> },
 *   questionIndex: number,
 *   totalQuestions: number,
 *   selectedKey: string | undefined,
 *   progress: number,
 *   canGoNext: boolean,
 *   isLastQuestion: boolean,
 *   onSelectAnswer: (key: string) => void,
 *   onNext: () => void,
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
  canGoNext,
  isLastQuestion,
  onSelectAnswer,
  onNext,
  onBack,
  onSkipQuestion,
}) {
  const { t } = useTranslation();

  return (
    <>
      <section aria-label={t("quiz.progress")} className="mb-8">
        <div className="mb-2 flex items-center justify-between text-sm text-slate-400">
          <span>{t("quiz.progress")}</span>
          <span className="tabular-nums text-emerald-300/90">{progress}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-600 via-teal-500 to-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.35)] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </section>

      <section className="rounded-2xl border border-white/[0.08] bg-black/25 p-5 shadow-inner backdrop-blur-sm md:p-6">
        <p className="mb-2 text-xs uppercase tracking-[0.14em] text-emerald-400/70">
          {question.section}
        </p>
        <h2 className="text-xl font-medium text-slate-50">
          {questionIndex + 1}. {question.prompt}
        </h2>

        <div className="mt-5 grid gap-3">
          {Object.entries(question.options).map(([key, text]) => {
            const active = selectedKey === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => onSelectAnswer(key)}
                className={`w-full rounded-xl border p-4 text-left text-sm leading-relaxed transition-all md:text-base ${
                  active
                    ? "border-emerald-400/50 bg-emerald-500/15 text-slate-50 shadow-[0_0_24px_rgba(52,211,153,0.15)]"
                    : "border-white/10 bg-white/[0.03] text-slate-200 hover:border-emerald-500/25 hover:bg-emerald-500/5"
                }`}
              >
                {text}
              </button>
            );
          })}
        </div>
      </section>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBack}
          disabled={questionIndex === 0}
          className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft size={16} /> {t("common.back")}
        </button>

        <div className="flex items-center gap-2">
          {onSkipQuestion ? (
            <button
              type="button"
              onClick={onSkipQuestion}
              className="rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:text-slate-200"
            >
              {t("quiz.skipQuestion")}
            </button>
          ) : null}
          <button
            type="button"
            onClick={onNext}
            disabled={!canGoNext}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500/90 to-amber-600/90 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-900/25 transition hover:from-amber-400 hover:to-amber-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLastQuestion ? t("quiz.seeResult") : t("common.next")} <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </>
  );
}

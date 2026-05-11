import { useMemo } from "react";
import { ChevronLeft, ChevronRight, FastForward, LogOut, X } from "lucide-react";
import { Trans, useTranslation } from "react-i18next";

import { DOSHA_MAP } from "../data/quizData.js";
import { getLocalizedQuestions } from "../i18n/quizI18n.js";
import { useAuthContext } from "../viewmodels/AuthContext.js";
import { useQuizViewModel } from "../viewmodels/useQuizViewModel.js";
import { LanguageToggleView } from "../views/LanguageToggleView.jsx";
import { QuizResultsView } from "../views/QuizResultsView.jsx";
import { QuizView } from "../views/QuizView.jsx";

/**
 * Composition root for the dosha quiz.
 *
 * @param {{
 *   onProfileSaved: (result: { user_id?: string }) => void,
 *   onCancel?: () => void,
 * }} props
 */
export function QuizContainer({ onProfileSaved, onCancel }) {
  const { t, i18n } = useTranslation();
  const auth = useAuthContext();
  const lang = (i18n.resolvedLanguage || i18n.language || "en").slice(0, 2);
  const localizedQuestions = useMemo(() => getLocalizedQuestions(lang), [lang]);
  const vm = useQuizViewModel({ onProfileSaved, questions: localizedQuestions, t });
  const isRetake = typeof onCancel === "function";

  const greeting = auth.user?.display_name || auth.user?.email || auth.user?.phone || "";

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink-900 p-4 md:p-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_75%_45%_at_50%_-15%,rgba(52,211,153,0.09),transparent_55%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-72 w-72 rounded-full bg-emerald-500/[0.06] blur-3xl" />
      <div className="pointer-events-none absolute left-0 top-1/3 h-48 w-48 rounded-full bg-vata/[0.04] blur-3xl" />

      <div className="relative mx-auto max-w-4xl rounded-[1.75rem] border border-white/[0.07] bg-white/[0.035] p-6 shadow-panel backdrop-blur-xl md:p-10">
        <header className="mb-10 space-y-6 border-b border-white/[0.06] pb-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-amber-200/55">
                {isRetake ? t("quiz.updateIntro") : t("quiz.welcomeIntro")}
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
                {t("quiz.header")}
              </h1>
              {greeting ? (
                <p className="mt-3 max-w-measure text-sm leading-relaxed text-slate-400">
                  <Trans
                    i18nKey="quiz.signedInAs"
                    values={{ name: greeting }}
                    components={{ bold: <span className="font-medium text-slate-200" /> }}
                  />
                </p>
              ) : null}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/[0.06] bg-black/35 p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-md">
            <div className="flex flex-wrap items-center gap-2">
              <LanguageToggleView />
              <span
                className="hidden h-7 w-px bg-white/10 sm:inline-block"
                aria-hidden
              />
              <div className="rounded-full border border-white/[0.08] bg-white/[0.04] px-3.5 py-1.5 text-xs font-medium text-slate-300">
                {vm.route === "quiz"
                  ? t("quiz.questionLabel", {
                      current: vm.questionIndex + 1,
                      total: localizedQuestions.length,
                    })
                  : t("quiz.resultLabel", {
                      dosha: vm.assessment
                        ? t(`quiz.doshaLabels.${vm.assessment.dominantDosha}`)
                        : "",
                    })}
              </div>
            </div>
            <div className="flex flex-1 flex-wrap items-center justify-end gap-2">
              {vm.route === "quiz" ? (
                <button
                  type="button"
                  onClick={vm.skipAssessment}
                  disabled={vm.submitting}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <FastForward className="h-3.5 w-3.5" aria-hidden /> {t("quiz.skipRest")}
                </button>
              ) : null}
              {isRetake ? (
                <button
                  type="button"
                  onClick={onCancel}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08]"
                >
                  <X className="h-3.5 w-3.5" aria-hidden /> {t("quiz.backToHub")}
                </button>
              ) : null}
              <button
                type="button"
                onClick={auth.logOut}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08]"
              >
                <LogOut className="h-3.5 w-3.5" aria-hidden /> {t("common.logOut")}
              </button>
            </div>
          </div>
        </header>

        {vm.submitError ? (
          <p
            role="alert"
            className="mb-4 rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200"
          >
            {vm.submitError}
          </p>
        ) : null}

        {vm.route === "quiz" && vm.currentQuestion ? (
          <QuizView
            question={vm.currentQuestion}
            questionIndex={vm.questionIndex}
            totalQuestions={localizedQuestions.length}
            selectedKey={vm.selectedKey}
            progress={vm.progress}
            onSelectAnswer={vm.selectAnswer}
            onBack={vm.goBack}
            onSkipQuestion={vm.skipQuestion}
          />
        ) : vm.assessment ? (
          <QuizResultsView
            scores={vm.assessment.scores}
            dominantDosha={vm.assessment.dominantDosha}
            onContinue={vm.submitProfile}
            continuing={vm.submitting}
            continueError={vm.submitError}
          />
        ) : null}
      </div>

      <span aria-hidden className="hidden">
        <ChevronLeft />
        <ChevronRight />
      </span>
    </main>
  );
}

// Keep dosha map import alive in case external tests still reference it.
export { DOSHA_MAP };

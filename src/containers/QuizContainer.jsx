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
    <main className="relative min-h-screen overflow-hidden bg-[#0b0d11] p-4 md:p-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(52,211,153,0.08),transparent)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-64 w-64 rounded-full bg-emerald-500/5 blur-3xl" />

      <div className="relative mx-auto max-w-4xl rounded-3xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl md:p-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-amber-200/60">
              {isRetake ? t("quiz.updateIntro") : t("quiz.welcomeIntro")}
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
              {t("quiz.header")}
            </h1>
            {greeting ? (
              <p className="mt-2 text-sm text-slate-400">
                <Trans
                  i18nKey="quiz.signedInAs"
                  values={{ name: greeting }}
                  components={{ bold: <span className="font-medium text-slate-200" /> }}
                />
              </p>
            ) : null}
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <LanguageToggleView />
            <div className="rounded-full border border-white/10 bg-black/30 px-4 py-2 text-sm font-medium text-slate-300">
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
            {vm.route === "quiz" ? (
              <button
                type="button"
                onClick={vm.skipAssessment}
                disabled={vm.submitting}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <FastForward className="h-3.5 w-3.5" /> {t("quiz.skipRest")}
              </button>
            ) : null}
            {isRetake ? (
              <button
                type="button"
                onClick={onCancel}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10"
              >
                <X className="h-3.5 w-3.5" /> {t("quiz.backToHub")}
              </button>
            ) : null}
            <button
              type="button"
              onClick={auth.logOut}
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10"
            >
              <LogOut className="h-3.5 w-3.5" /> {t("common.logOut")}
            </button>
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
            canGoNext={vm.canGoNext}
            isLastQuestion={vm.isLastQuestion}
            onSelectAnswer={vm.selectAnswer}
            onNext={vm.goNext}
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

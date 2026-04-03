import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { clearHolisticaSession, getStoredUserId, setStoredUserId, upsertProfile } from "./api";
import { DailyCheckIn } from "./components/DailyCheckIn";
import { HealthChat } from "./components/HealthChat";
import { QuizResults } from "./components/QuizResults";
import { WeeklyPlanPanel } from "./components/WeeklyPlanPanel";
import { DOSHA_MAP, DOSHA_LABELS, QUIZ_QUESTIONS } from "./data/quizData";

const ONBOARDING_STORAGE_KEY = "holistica_has_completed_onboarding";

/** One-shot per full page load: `?reset=1` or `?quiz=1` clears session and opens the quiz. */
let quizResetFromUrlConsumed = false;

function consumeQuizResetFromUrl() {
  if (quizResetFromUrlConsumed || typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  const wantsReset = params.has("reset") || params.get("quiz") === "1";
  if (!wantsReset) return false;
  quizResetFromUrlConsumed = true;
  clearHolisticaSession();
  const path = window.location.pathname || "/";
  window.history.replaceState({}, "", path);
  return true;
}

function getOnboardingCompleted() {
  try {
    return localStorage.getItem(ONBOARDING_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function setOnboardingCompleted(value) {
  try {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, value ? "true" : "false");
  } catch {
    // ignore
  }
}

function buildAssessment(answers) {
  const scores = { vata: 0, pitta: 0, kapha: 0 };
  const rawQuizData = {};

  QUIZ_QUESTIONS.forEach((q) => {
    const selected = answers[q.id];
    if (!selected) return;
    const dosha = DOSHA_MAP[selected];
    if (dosha) scores[dosha] += 1;
    rawQuizData[q.id] = q.options[selected];
  });

  const dominantDosha = Object.keys(scores).reduce((best, current) =>
    scores[current] > scores[best] ? current : best
  );

  return {
    dominantDosha,
    scores,
    rawQuizData,
  };
}

function createProfilePayload(assessment, answers, existingUserId) {
  const selectedAnswers = QUIZ_QUESTIONS.map((q) => ({
    question_id: q.id,
    question_text: q.prompt,
    selected_option_key: answers[q.id],
    selected_option_text: answers[q.id] ? q.options[answers[q.id]] : null,
  }));

  return {
    ...(existingUserId ? { user_id: existingUserId } : {}),
    consent_flags: {
      prakriti_quiz_completed: true,
      app: "holistica_web",
    },
    prakriti_quiz: {
      dominant_dosha: assessment.dominantDosha,
      dosha_distribution: assessment.scores,
      raw_quiz_data: assessment.rawQuizData,
      selected_answers: selectedAnswers,
      completed_at: new Date().toISOString(),
    },
  };
}

function App() {
  const [backendUserId, setBackendUserId] = useState(() => {
    const forced = consumeQuizResetFromUrl();
    return forced ? null : getStoredUserId();
  });
  const [route, setRoute] = useState(() => {
    consumeQuizResetFromUrl();
    const hasDone = getOnboardingCompleted();
    const storedUserId = getStoredUserId();
    return hasDone && storedUserId ? "chat" : "quiz";
  });
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [assessment, setAssessment] = useState(null);
  const [continueLoading, setContinueLoading] = useState(false);
  const [continueError, setContinueError] = useState(null);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const progress = Math.round((answeredCount / QUIZ_QUESTIONS.length) * 100);
  const currentQuestion = QUIZ_QUESTIONS[questionIndex];
  const selectedKey = answers[currentQuestion.id];

  const canGoNext = Boolean(selectedKey);
  const isLastQuestion = questionIndex === QUIZ_QUESTIONS.length - 1;

  const goNext = () => {
    if (!canGoNext) return;
    if (isLastQuestion) {
      const built = buildAssessment(answers);
      setAssessment(built);
      setRoute("results");
      return;
    }
    setQuestionIndex((prev) => prev + 1);
  };

  const goBack = () => {
    setQuestionIndex((prev) => Math.max(0, prev - 1));
  };

  const handleAnswer = (key) => {
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: key }));
  };

  const handleContinueToPlan = async () => {
    if (!assessment) return;
    setContinueError(null);
    setContinueLoading(true);
    try {
      const payload = createProfilePayload(assessment, answers, backendUserId || undefined);
      const result = await upsertProfile(payload);
      setStoredUserId(result.user_id);
      setBackendUserId(result.user_id);
      setOnboardingCompleted(true);
      setRoute("chat");
    } catch (error) {
      setContinueError(error instanceof Error ? error.message : "Could not save your profile.");
    } finally {
      setContinueLoading(false);
    }
  };

  const restartOnboarding = () => {
    clearHolisticaSession();
    setBackendUserId(null);
    setRoute("quiz");
    setQuestionIndex(0);
    setAnswers({});
    setAssessment(null);
    setContinueError(null);
  };

  if (route === "chat") {
    return (
      <main className="min-h-screen bg-[#0b0d11] p-4 md:p-8">
        <div className="mx-auto max-w-6xl space-y-8">
          <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-amber-200/60">HolisticAI Health</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-50 md:text-4xl">
                Your wellness hub
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
                Daily check-in, your weekly Ayurvedic-inspired plan, and grounded chat — all tailored to
                your profile.
              </p>
            </div>
            <button
              type="button"
              onClick={restartOnboarding}
              className="shrink-0 self-start rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10"
            >
              Retake dosha quiz
            </button>
          </header>

          <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
            <div className="space-y-6 lg:col-span-5">
              <DailyCheckIn userId={backendUserId} />
              <WeeklyPlanPanel userId={backendUserId} />
            </div>
            <div className="lg:col-span-7">
              <div className="rounded-3xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl md:p-8">
                <p className="text-xs uppercase tracking-[0.2em] text-emerald-400/70">Assistant</p>
                <h2 className="mt-1 text-xl font-semibold text-slate-50">Personalized chat</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Non-diagnostic guidance with search-backed citations when available.
                </p>
                <div className="mt-5">
                  <HealthChat userId={backendUserId} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0d11] p-4 md:p-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(52,211,153,0.08),transparent)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-64 w-64 rounded-full bg-emerald-500/5 blur-3xl" />

      <div className="relative mx-auto max-w-4xl rounded-3xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl md:p-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-amber-200/60">First-time onboarding</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
              35-Question Dosha Assessment
            </h1>
          </div>
          <div className="shrink-0 rounded-full border border-white/10 bg-black/30 px-4 py-2 text-sm font-medium text-slate-300">
            {route === "quiz"
              ? `Question ${questionIndex + 1} of ${QUIZ_QUESTIONS.length}`
              : `Result: ${assessment ? DOSHA_LABELS[assessment.dominantDosha] : ""}`}
          </div>
        </header>

        {route === "quiz" ? (
          <>
            <section aria-label="Quiz progress" className="mb-8">
              <div className="mb-2 flex items-center justify-between text-sm text-slate-400">
                <span>Progress</span>
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
                {currentQuestion.section}
              </p>
              <h2 className="text-xl font-medium text-slate-50">
                {questionIndex + 1}. {currentQuestion.prompt}
              </h2>

              <div className="mt-5 grid gap-3">
                {Object.entries(currentQuestion.options).map(([key, text]) => {
                  const active = selectedKey === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => handleAnswer(key)}
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

            <div className="mt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={goBack}
                disabled={questionIndex === 0}
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft size={16} /> Back
              </button>

              <button
                type="button"
                onClick={goNext}
                disabled={!canGoNext}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500/90 to-amber-600/90 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-amber-900/25 transition hover:from-amber-400 hover:to-amber-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isLastQuestion ? "See my result" : "Next"} <ChevronRight size={16} />
              </button>
            </div>
          </>
        ) : assessment ? (
          <QuizResults
            scores={assessment.scores}
            dominantDosha={assessment.dominantDosha}
            onContinue={handleContinueToPlan}
            continuing={continueLoading}
            continueError={continueError}
          />
        ) : null}
      </div>
    </main>
  );
}

export default App;

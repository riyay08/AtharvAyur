import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { getStoredUserId, setStoredUserId, upsertProfile } from "./api";
import { HealthChat } from "./components/HealthChat";
import { QuizResults } from "./components/QuizResults";
import { DOSHA_MAP, DOSHA_LABELS, QUIZ_QUESTIONS } from "./data/quizData";

const ONBOARDING_STORAGE_KEY = "holistica_has_completed_onboarding";

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
  const [backendUserId, setBackendUserId] = useState(() => getStoredUserId());
  const [route, setRoute] = useState(() => {
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

  if (route === "chat") {
    return (
      <main className="min-h-screen bg-gradient-to-b from-cyan-50 via-orange-50 to-green-50 p-4 md:p-8">
        <div className="mx-auto max-w-5xl rounded-3xl border border-white/50 bg-white/85 p-5 shadow-wellness backdrop-blur md:p-8">
          <header className="mb-5">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">HolisticAI Health</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900 md:text-3xl">
              Your Personalized Chat Plan
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              Ask wellness questions and receive grounded, non-diagnostic guidance tailored to your
              onboarding profile.
            </p>
          </header>
          <HealthChat userId={backendUserId} />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-cyan-50 via-orange-50 to-green-50 p-4 md:p-8">
      <div className="mx-auto max-w-4xl rounded-3xl border border-white/50 bg-white/85 p-5 shadow-wellness backdrop-blur md:p-8">
        <header className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">First-time onboarding</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900 md:text-3xl">
              35-Question Dosha Assessment
            </h1>
          </div>
          <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">
            {route === "quiz"
              ? `Question ${questionIndex + 1} of ${QUIZ_QUESTIONS.length}`
              : `Result: ${assessment ? DOSHA_LABELS[assessment.dominantDosha] : ""}`}
          </div>
        </header>

        {route === "quiz" ? (
          <>
            <section aria-label="Quiz progress" className="mb-8">
              <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-vata via-pitta to-kapha transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200/70 bg-white p-5 md:p-6">
              <p className="mb-2 text-xs uppercase tracking-[0.14em] text-slate-500">
                {currentQuestion.section}
              </p>
              <h2 className="text-xl font-medium text-slate-900">
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
                          ? "border-slate-900 bg-slate-50 shadow-sm"
                          : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm"
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
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ChevronLeft size={16} /> Back
              </button>

              <button
                type="button"
                onClick={goNext}
                disabled={!canGoNext}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
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

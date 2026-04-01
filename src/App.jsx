import { useMemo, useState } from "react";
import { CheckCircle2, ChevronLeft, ChevronRight, Leaf, Loader2 } from "lucide-react";
import {
  clearStoredUserId,
  getStoredUserId,
  setStoredUserId,
  upsertProfile,
} from "./api";
import { HealthChat } from "./components/HealthChat";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const QUESTIONS = [
  {
    prompt: "How would you describe your natural body frame and weight?",
    options: {
      A: "Slim or thin; I find it very hard to gain weight or muscle.",
      B: "Medium or athletic; I stay fairly toned and gain/lose weight with effort.",
      C: "Large or \"sturdy\"; I gain weight easily and find it very hard to lose.",
    },
  },
  {
    prompt: "Which best describes your typical appetite and digestion?",
    options: {
      A: "Irregular; I often forget to eat or feel bloated/gassy after meals.",
      B: "Intense; I get \"hangry\" if I miss a meal and have a very strong thirst.",
      C: "Steady but slow; I can skip meals easily but often feel heavy after eating.",
    },
  },
  {
    prompt: "What is your most common sleep pattern?",
    options: {
      A: "Light or restless; I wake up easily and often have trouble falling back asleep.",
      B: "Sound and efficient; I sleep deeply but don't need more than 6–7 hours.",
      C: "Heavy and long; I hate waking up and often feel \"foggy\" even after 8+ hours.",
    },
  },
  {
    prompt: "How do you typically react when you are under significant stress?",
    options: {
      A: "I get anxious, worried, or my mind starts racing with \"what-ifs.\"",
      B: "I become irritable, impatient, or perfectionistic.",
      C: "I shut down, withdraw, or feel unmotivated and \"stuck.\"",
    },
  },
  {
    prompt: "How would you describe your natural energy levels throughout the day?",
    options: {
      A: "Bursts of high energy followed by sudden \"crashes\" or fatigue.",
      B: "Steady and goal-oriented; I have high stamina when I’m focused.",
      C: "Slow to start in the morning, but I have great long-term endurance.",
    },
  },
  {
    prompt: "Which climate or environment do you feel most comfortable in?",
    options: {
      A: "I prefer warm, humid weather; I am almost always the person who is \"cold.\"",
      B: "I prefer cool or breezy environments; I overheat easily and sweat a lot.",
      C: "I prefer dry, warm weather; I feel most sluggish in cold, damp conditions.",
    },
  },
];

const DOSHA_META = {
  VATA: {
    color: "vata",
    label: "Vata",
    description:
      "Prioritize Stress & Sleep modules. Focus on 'Grounding' routines and warm, cooked foods.",
  },
  PITTA: {
    color: "pitta",
    label: "Pitta",
    description:
      "Prioritize GI & Metabolic modules. Focus on 'Cooling' routines and moderation.",
  },
  KAPHA: {
    color: "kapha",
    label: "Kapha",
    description:
      "Prioritize Metabolic & Weight modules. Focus on 'Stimulating' routines and movement.",
  },
};

const CHOICE_TO_DOSHA = { A: "VATA", B: "PITTA", C: "KAPHA" };

const initialScores = { VATA: 0, PITTA: 0, KAPHA: 0 };

function App() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [backendUserId, setBackendUserId] = useState(() => getStoredUserId());
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [profileSavedAt, setProfileSavedAt] = useState(null);
  const [chatMountKey, setChatMountKey] = useState(0);
  const isComplete = step >= QUESTIONS.length;

  const scores = useMemo(() => {
    const tally = { ...initialScores };
    Object.values(answers).forEach((choice) => {
      const dosha = CHOICE_TO_DOSHA[choice];
      if (dosha) tally[dosha] += 1;
    });
    return tally;
  }, [answers]);

  const primaryDosha = useMemo(() => {
    return Object.keys(scores).reduce((maxKey, current) =>
      scores[current] > scores[maxKey] ? current : maxKey
    );
  }, [scores]);

  const progress = Math.round((Object.keys(answers).length / QUESTIONS.length) * 100);

  const handleAnswer = (choice) => {
    setAnswers((prev) => ({ ...prev, [step]: choice }));
  };

  const goNext = () => {
    if (!answers[step]) return;
    setStep((prev) => prev + 1);
  };

  const goBack = () => {
    setStep((prev) => Math.max(0, prev - 1));
  };

  const restart = () => {
    setAnswers({});
    setStep(0);
    clearStoredUserId();
    setBackendUserId(null);
    setProfileError(null);
    setProfileSavedAt(null);
    setChatMountKey((k) => k + 1);
  };

  const saveProfileToBackend = async () => {
    setProfileSaving(true);
    setProfileError(null);
    try {
      const existingId = backendUserId || undefined;
      const letter = Object.entries(CHOICE_TO_DOSHA).find(([, d]) => d === primaryDosha)?.[0];
      const payload = {
        ...(existingId ? { user_id: existingId } : {}),
        consent_flags: { prakriti_quiz_completed: true, app: "holistica_web" },
        prakriti_quiz: {
          scores: { VATA: scores.VATA, PITTA: scores.PITTA, KAPHA: scores.KAPHA },
          primary_dosha: primaryDosha,
          primary_choice_letter: letter,
          answers,
        },
      };
      const res = await upsertProfile(payload);
      const id = res.user_id;
      setStoredUserId(id);
      setBackendUserId(id);
      setProfileSavedAt(new Date().toISOString());
      setChatMountKey((k) => k + 1);
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : "Could not save profile");
    } finally {
      setProfileSaving(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-cyan-50 via-orange-50 to-green-50 p-4 md:p-8">
      <div className="mx-auto max-w-4xl rounded-3xl border border-white/50 bg-white/85 p-5 shadow-wellness backdrop-blur md:p-8">
        <header className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Onboarding</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900 md:text-3xl">
              Prakriti (Dosha) Quiz
            </h1>
          </div>
          <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">
            {isComplete ? "Completed" : `Question ${step + 1} of ${QUESTIONS.length}`}
          </div>
        </header>

        {!isComplete ? (
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
              <h2 className="text-xl font-medium text-slate-900">
                {step + 1}. {QUESTIONS[step].prompt}
              </h2>

              <div className="mt-5 grid gap-3">
                {Object.entries(QUESTIONS[step].options).map(([key, text]) => {
                  const active = answers[step] === key;
                  const colorClass =
                    key === "A"
                      ? "border-vata/70 bg-vata/15"
                      : key === "B"
                        ? "border-pitta/70 bg-pitta/15"
                        : "border-kapha/70 bg-kapha/15";

                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => handleAnswer(key)}
                      className={`w-full rounded-xl border p-4 text-left transition-all hover:-translate-y-[1px] hover:shadow-md ${
                        active ? colorClass : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                    >
                      <span className="mb-1 block text-sm font-semibold text-slate-800">{key})</span>
                      <span className="text-sm leading-relaxed text-slate-700 md:text-base">{text}</span>
                    </button>
                  );
                })}
              </div>
            </section>

            <div className="mt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={goBack}
                disabled={step === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ChevronLeft size={16} /> Back
              </button>

              <button
                type="button"
                onClick={goNext}
                disabled={!answers[step]}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {step === QUESTIONS.length - 1 ? "See Results" : "Next"} <ChevronRight size={16} />
              </button>
            </div>
          </>
        ) : (
          <>
          <section className="grid gap-6 lg:grid-cols-2">
            <article className="rounded-2xl border border-slate-200/70 bg-white p-5 md:p-6">
              <p className="text-sm text-slate-500">Dosha Distribution</p>
              <div className="mt-3 h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart
                    data={[
                      { name: "Vata", score: scores.VATA, fill: "#7EC8E3" },
                      { name: "Pitta", score: scores.PITTA, fill: "#D98C6B" },
                      { name: "Kapha", score: scores.KAPHA, fill: "#8FAF7A" },
                    ]}
                  >
                    <PolarGrid stroke="#d1d5db" />
                    <PolarAngleAxis dataKey="name" tick={{ fill: "#334155", fontSize: 12 }} />
                    <Radar
                      name="Score"
                      dataKey="score"
                      stroke="#0f172a"
                      fill="#475569"
                      fillOpacity={0.25}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="rounded-2xl border border-slate-200/70 bg-white p-5 md:p-6">
              <p className="text-sm text-slate-500">Primary Persona</p>
              <div className="mt-3 flex items-center gap-3">
                <div
                  className={`rounded-full p-2 ${
                    primaryDosha === "VATA"
                      ? "bg-vata/25 text-cyan-700"
                      : primaryDosha === "PITTA"
                        ? "bg-pitta/25 text-orange-700"
                        : "bg-kapha/25 text-green-700"
                  }`}
                >
                  {primaryDosha === "VATA" ? <Leaf size={20} /> : <CheckCircle2 size={20} />}
                </div>
                <h2 className="text-2xl font-semibold text-slate-900">
                  Mostly {Object.entries(CHOICE_TO_DOSHA).find(([, d]) => d === primaryDosha)?.[0]}
                  's ({DOSHA_META[primaryDosha].label})
                </h2>
              </div>

              <p className="mt-4 text-sm leading-relaxed text-slate-700 md:text-base">
                {DOSHA_META[primaryDosha].description}
              </p>

              <div className="mt-6 grid grid-cols-3 gap-3 text-center">
                <ScorePill label="Vata" score={scores.VATA} color="bg-vata/25 text-cyan-800" />
                <ScorePill label="Pitta" score={scores.PITTA} color="bg-pitta/25 text-orange-800" />
                <ScorePill label="Kapha" score={scores.KAPHA} color="bg-kapha/25 text-green-800" />
              </div>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <button
                  type="button"
                  onClick={saveProfileToBackend}
                  disabled={profileSaving}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-900 disabled:opacity-60"
                >
                  {profileSaving ? <Loader2 className="animate-spin" size={16} /> : null}
                  {backendUserId ? "Update profile on server" : "Save profile & enable chat"}
                </button>
                <button
                  type="button"
                  onClick={restart}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Retake Quiz
                </button>
              </div>
              {profileError && (
                <p className="mt-3 text-sm text-red-600" role="alert">
                  {profileError}
                </p>
              )}
              {profileSavedAt && !profileError && (
                <p className="mt-3 text-xs text-emerald-700">
                  Profile synced. Chat is available below{backendUserId ? ` (user id stored locally).` : "."}
                </p>
              )}
            </article>
          </section>

          <section className="mt-8" aria-label="HolisticAI chat">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Ask HolisticAI</h2>
            <HealthChat key={chatMountKey} userId={backendUserId} />
          </section>
          </>
        )}
      </div>
    </main>
  );
}

function ScorePill({ label, score, color }) {
  return (
    <div className={`rounded-xl p-3 ${color}`}>
      <p className="text-xs uppercase tracking-wide">{label}</p>
      <p className="text-xl font-semibold">{score}</p>
    </div>
  );
}

export default App;

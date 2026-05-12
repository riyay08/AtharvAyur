import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const LINE_KEYS = ["quiz.analyzing.line1", "quiz.analyzing.line2", "quiz.analyzing.line3"];

/**
 * @param {{ holdMs?: number }} props
 */
export function QuizAnalyzingView({ holdMs = 3000 }) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  const intervalMs = Math.max(800, Math.floor(holdMs / 3));

  useEffect(() => {
    const id = setInterval(() => {
      setStep((s) => (s < LINE_KEYS.length - 1 ? s + 1 : s));
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return (
    <section
      aria-busy="true"
      aria-live="polite"
      className="flex min-h-[280px] flex-col items-center justify-center rounded-2xl border border-white/[0.08] bg-black/30 px-6 py-12 text-center backdrop-blur-md md:min-h-[320px]"
    >
      <div
        className="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl border border-sage-400/35 bg-gradient-to-br from-sage-500/25 to-emerald-600/10 shadow-[0_0_32px_rgba(138,159,120,0.35)] animate-wellness-pulse"
        aria-hidden
      >
        <span className="text-2xl font-semibold tracking-tight text-sage-100">ॐ</span>
      </div>
      <h2 className="text-lg font-semibold text-slate-100 md:text-xl">{t("quiz.analyzing.title")}</h2>
      <p className="mt-3 max-w-md text-sm text-sage-200/90 md:text-base">{t(LINE_KEYS[step])}</p>
      <div className="mt-8 flex gap-1.5" aria-hidden>
        {LINE_KEYS.map((k, i) => (
          <span
            key={k}
            className={`h-1.5 w-8 rounded-full transition-colors ${
              i === step ? "bg-sage-400" : "bg-white/15"
            }`}
          />
        ))}
      </div>
    </section>
  );
}

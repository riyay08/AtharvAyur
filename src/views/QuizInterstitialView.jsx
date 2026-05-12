import { ChevronLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * @param {{
 *   slot: 1 | 2 | 3,
 *   leanKey?: 'vata' | 'pitta' | 'kapha' | null,
 *   onContinue: () => void,
 *   onBack: () => void,
 * }} props
 */
export function QuizInterstitialView({ slot, leanKey, onContinue, onBack }) {
  const { t } = useTranslation();

  let body = t("quiz.interstitial.after1.body");
  if (slot === 1) {
    body = t("quiz.interstitial.after1.body");
  } else if (slot === 2) {
    if (leanKey === "pitta") body = t("quiz.interstitial.after2.bodyPitta");
    else if (leanKey === "vata") body = t("quiz.interstitial.after2.bodyVata");
    else if (leanKey === "kapha") body = t("quiz.interstitial.after2.bodyKapha");
    else body = t("quiz.interstitial.after2.body");
  } else {
    body = t("quiz.interstitial.after3.body");
  }

  const continueKey =
    slot === 1
      ? "quiz.interstitial.continueToChapter2"
      : slot === 2
        ? "quiz.interstitial.continueToChapter3"
        : "quiz.interstitial.continueToChapter4";

  return (
    <>
      <section
        aria-label={t("quiz.interstitial.aria")}
        className="rounded-2xl border border-sage-300/25 bg-gradient-to-br from-white/[0.07] to-sage-500/5 p-6 shadow-[0_0_40px_rgba(106,127,94,0.12)] backdrop-blur-xl md:p-8"
      >
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-sage-300/90">
          {t("quiz.interstitial.kicker")}
        </p>
        <p className="mt-4 text-base leading-relaxed text-slate-200 md:text-lg">{body}</p>
      </section>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-white/25 hover:bg-white/10"
        >
          <ChevronLeft size={16} /> {t("common.back")}
        </button>
        <button
          type="button"
          onClick={onContinue}
          className="inline-flex items-center gap-2 rounded-xl border border-sage-400/50 bg-sage-500/20 px-5 py-2.5 text-sm font-semibold text-sage-50 shadow-[0_0_24px_rgba(138,159,120,0.25)] transition hover:border-sage-300/60 hover:bg-sage-500/30"
        >
          {t(continueKey)}
        </button>
      </div>
    </>
  );
}

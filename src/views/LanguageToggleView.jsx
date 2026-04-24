import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";

import { SUPPORTED_LANGS } from "../i18n";

/**
 * Compact language toggle. Persists the choice automatically through
 * i18next's localStorage detector. Renders nothing if only one language
 * is configured.
 *
 * @param {{ size?: "sm" | "md", className?: string }} props
 */
export function LanguageToggleView({ size = "sm", className = "" }) {
  const { t, i18n } = useTranslation();
  if (SUPPORTED_LANGS.length < 2) return null;

  const active = (i18n.resolvedLanguage || i18n.language || "en").slice(0, 2);
  const padding = size === "md" ? "px-2.5 py-1.5 text-sm" : "px-2 py-1 text-xs";

  return (
    <div
      className={`inline-flex items-center gap-1 rounded-full border border-white/10 bg-black/30 p-0.5 backdrop-blur ${className}`}
      role="group"
      aria-label={t("language.label")}
    >
      <span className="pl-1.5 pr-0.5 text-slate-500" aria-hidden>
        <Languages size={size === "md" ? 14 : 12} />
      </span>
      {SUPPORTED_LANGS.map((lng) => {
        const isActive = lng === active;
        return (
          <button
            key={lng}
            type="button"
            onClick={() => i18n.changeLanguage(lng)}
            aria-pressed={isActive}
            className={`rounded-full font-medium transition ${padding} ${
              isActive
                ? "bg-emerald-500/20 text-emerald-100 shadow-inner"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {lng === "hi" ? t("language.hindi") : t("language.english")}
          </button>
        );
      })}
    </div>
  );
}

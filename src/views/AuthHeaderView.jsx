import { ClipboardList, LogOut, Shield, User as UserIcon } from "lucide-react";
import { useTranslation } from "react-i18next";

import { LanguageToggleView } from "./LanguageToggleView.jsx";

/**
 * Pure header bar shown above the wellness hub. The hub is auth-only,
 * so this only renders the signed-in state.
 *
 * @param {{
 *   user: any|null,
 *   isAuthenticated: boolean,
 *   onOpenSecurity: () => void,
 *   onLogOut: () => void,
 *   onRestartOnboarding: () => void,
 * }} props
 */
export function AuthHeaderView({
  user,
  isAuthenticated,
  onOpenSecurity,
  onLogOut,
  onRestartOnboarding,
}) {
  const { t } = useTranslation();
  const label =
    user?.display_name ||
    user?.email ||
    user?.phone ||
    (isAuthenticated ? t("security.signedInAs") : "");

  return (
    <header className="flex flex-col gap-6 border-b border-white/[0.06] pb-8 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-amber-200/55">
          {t("brand.appTagline")}
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-50 md:text-[2.25rem] md:leading-tight">
          {t("header.hubTitle")}
        </h1>
        <p className="mt-3 max-w-measure text-sm leading-relaxed text-slate-400">
          {t("header.hubSubtitle")}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 self-start sm:max-w-[min(100%,24rem)] sm:justify-end">
        <LanguageToggleView />
        {isAuthenticated ? (
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-200">
            <UserIcon className="h-3.5 w-3.5" />
            {label}
          </span>
        ) : null}
        <button
          type="button"
          onClick={onRestartOnboarding}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08]"
        >
          <ClipboardList className="h-3.5 w-3.5" /> {t("header.updateAssessment")}
        </button>
        <button
          type="button"
          onClick={onOpenSecurity}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08]"
        >
          <Shield className="h-3.5 w-3.5" /> {t("header.security")}
        </button>
        <button
          type="button"
          onClick={onLogOut}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/22 hover:bg-white/[0.08]"
        >
          <LogOut className="h-3.5 w-3.5" /> {t("common.logOut")}
        </button>
      </div>
    </header>
  );
}

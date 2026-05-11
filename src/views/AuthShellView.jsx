import { useTranslation } from "react-i18next";

import { LanguageToggleView } from "./LanguageToggleView.jsx";

/**
 * Pure shell that frames the login & signup screens with a consistent
 * background, header, and side-by-side layout. The container drops the
 * actual `LoginView`/`SignUpView` into `children`.
 */
export function AuthShellView({ mode, onSwitchMode, children, footer }) {
  const { t } = useTranslation();

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink-900 p-4 md:p-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_75%_45%_at_50%_-15%,rgba(52,211,153,0.09),transparent_55%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-72 w-72 rounded-full bg-emerald-500/[0.06] blur-3xl" />

      <div className="relative mx-auto flex min-h-[80vh] max-w-md flex-col justify-center">
        <div className="rounded-[1.75rem] border border-white/[0.07] bg-white/[0.035] p-6 shadow-panel backdrop-blur-xl md:p-8">
          <header className="mb-6 space-y-1">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.28em] text-amber-200/60">
                {t("brand.appName")}
              </p>
              <LanguageToggleView />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
              {mode === "signup" ? t("auth.signupTitle") : t("auth.loginTitle")}
            </h1>
            <p className="text-sm text-slate-400">
              {mode === "signup" ? t("auth.signupSubtitle") : t("auth.loginSubtitle")}
            </p>
          </header>

          {children}

          <div className="mt-6 flex items-center justify-between text-xs text-slate-400">
            <span>{mode === "signup" ? t("auth.hasAccount") : t("auth.noAccount")}</span>
            <button
              type="button"
              onClick={onSwitchMode}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 font-medium text-slate-100 transition hover:border-white/25 hover:bg-white/10"
            >
              {mode === "signup" ? t("auth.switchToLogin") : t("auth.switchToSignup")}
            </button>
          </div>

          {footer ? <div className="mt-4 text-center text-xs text-slate-500">{footer}</div> : null}
        </div>
      </div>
    </main>
  );
}

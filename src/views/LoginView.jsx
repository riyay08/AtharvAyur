import { useEffect, useRef } from "react";
import { Fingerprint, KeyRound, Loader2, Mail, Phone } from "lucide-react";
import { useTranslation } from "react-i18next";

import { renderGoogleSignInButton } from "../services/googleSignInService.js";
import { AuthTabsView } from "./AuthTabsView.jsx";

const FIELD =
  "w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-slate-50 placeholder:text-slate-500 outline-none transition focus:border-emerald-300/40 focus:bg-black/60";
const PRIMARY_BTN =
  "inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500/90 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-400";
const SECONDARY_BTN =
  "inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-100 transition hover:border-white/25 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50";

/**
 * Pure presentational login form. All state + behavior live in
 * `useLoginViewModel`; this component only renders + dispatches.
 */
export function LoginView({ vm, googleClientId, passkeySupported, onGoogleToken }) {
  const { t } = useTranslation();
  const googleHostRef = useRef(/** @type {HTMLDivElement|null} */ (null));

  useEffect(() => {
    if (!googleClientId || !googleHostRef.current) return;
    let cancelled = false;
    const host = googleHostRef.current;
    host.innerHTML = "";
    const wrappedCallback = (id) => {
      if (!cancelled) onGoogleToken?.(id);
    };
    window.__atharvayur_google_login_cb = wrappedCallback;
    renderGoogleSignInButton(host, { clientId: googleClientId }).catch(() => {});
    return () => {
      cancelled = true;
      delete window.__atharvayur_google_login_cb;
    };
  }, [googleClientId, onGoogleToken]);

  const tabs = [
    { id: "email", label: t("auth.tabs.email") },
    { id: "phone", label: t("auth.tabs.phone") },
    { id: "passkey", label: t("auth.tabs.passkey"), disabled: !passkeySupported },
  ];

  return (
    <div>
      <AuthTabsView tabs={tabs} activeId={vm.tab} onChange={vm.switchTab} />

      {vm.tab === "email" ? (
        <form className="space-y-3" onSubmit={vm.submitEmail} noValidate>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-400" htmlFor="login-email">
            {t("common.email")}
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              id="login-email"
              type="email"
              inputMode="email"
              autoComplete="email"
              className={`${FIELD} pl-9`}
              placeholder={t("auth.emailPlaceholder")}
              value={vm.email}
              onChange={(e) => vm.setEmail(e.target.value)}
              disabled={vm.submitting}
            />
          </div>

          <label className="block text-xs font-medium uppercase tracking-wide text-slate-400" htmlFor="login-password">
            {t("common.password")}
          </label>
          <div className="relative">
            <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              className={`${FIELD} pl-9`}
              placeholder={t("auth.passwordPlaceholder")}
              value={vm.password}
              onChange={(e) => vm.setPassword(e.target.value)}
              disabled={vm.submitting}
            />
          </div>

          <button type="submit" className={PRIMARY_BTN} disabled={!vm.canSubmitEmail || vm.submitting}>
            {vm.submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {t("common.logIn")}
          </button>
        </form>
      ) : null}

      {vm.tab === "phone" ? (
        <div className="space-y-3">
          <form className="space-y-3" onSubmit={vm.submitPhoneRequest} noValidate>
            <label className="block text-xs font-medium uppercase tracking-wide text-slate-400" htmlFor="login-phone">
              {t("common.phoneNumber")}
            </label>
            <div className="relative">
              <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                id="login-phone"
                type="tel"
                autoComplete="tel"
                className={`${FIELD} pl-9`}
                placeholder={t("auth.phonePlaceholder")}
                value={vm.phone}
                onChange={(e) => vm.setPhone(e.target.value)}
                disabled={vm.submitting || vm.otpRequested}
              />
            </div>
            {!vm.otpRequested ? (
              <button
                type="submit"
                className={SECONDARY_BTN}
                disabled={!vm.canSubmitPhoneRequest || vm.submitting}
              >
                {vm.submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {t("auth.sendOtp")}
              </button>
            ) : null}
          </form>

          {vm.otpRequested ? (
            <form className="space-y-3" onSubmit={vm.submitPhoneVerify} noValidate>
              <label className="block text-xs font-medium uppercase tracking-wide text-slate-400" htmlFor="login-otp">
                {t("auth.otpLabel")}
              </label>
              <input
                id="login-otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className={FIELD}
                placeholder={t("auth.otpPlaceholder")}
                value={vm.otp}
                onChange={(e) => vm.setOtp(e.target.value)}
                disabled={vm.submitting}
              />
              <button
                type="submit"
                className={PRIMARY_BTN}
                disabled={!vm.canSubmitPhoneVerify || vm.submitting}
              >
                {vm.submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {t("auth.verifyOtp")}
              </button>
            </form>
          ) : null}
        </div>
      ) : null}

      {vm.tab === "passkey" ? (
        <div className="space-y-3">
          <p className="text-sm text-slate-400">{t("auth.passkeyDescription")}</p>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-400" htmlFor="login-passkey-email">
            {t("auth.passkeyEmailHint")}
          </label>
          <input
            id="login-passkey-email"
            type="email"
            inputMode="email"
            autoComplete="email"
            className={FIELD}
            placeholder={t("auth.emailPlaceholder")}
            value={vm.email}
            onChange={(e) => vm.setEmail(e.target.value)}
            disabled={vm.submitting}
          />
          <button
            type="button"
            className={PRIMARY_BTN}
            onClick={vm.submitPasskey}
            disabled={vm.submitting || !passkeySupported}
          >
            {vm.submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Fingerprint className="h-4 w-4" />}
            {t("auth.passkeyContinue")}
          </button>
          {!passkeySupported ? (
            <p className="text-xs text-amber-300/80">{t("auth.passkeyUnsupported")}</p>
          ) : null}
        </div>
      ) : null}

      {googleClientId ? (
        <div className="mt-5 space-y-2">
          <div className="flex items-center gap-3 text-xs uppercase tracking-widest text-slate-500">
            <span className="h-px flex-1 bg-white/10" />
            <span>{t("common.or")}</span>
            <span className="h-px flex-1 bg-white/10" />
          </div>
          <div ref={googleHostRef} className="flex justify-center" />
        </div>
      ) : null}

      {vm.error ? (
        <p role="alert" className="mt-4 rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {vm.error}
        </p>
      ) : null}
      {vm.info ? (
        <p className="mt-4 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {vm.info}
        </p>
      ) : null}
    </div>
  );
}

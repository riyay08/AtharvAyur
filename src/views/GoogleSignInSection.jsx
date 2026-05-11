import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import { renderGoogleSignInButton } from "../services/googleSignInService.js";
import { isGoogleSignInDisabledByEnv } from "../utils/googleSignInEnv.js";

/**
 * Google Identity Services button + optional dev hint when `VITE_GOOGLE_CLIENT_ID` is unset.
 *
 * @param {{ googleClientId: string | null | undefined, onGoogleToken: (idToken: string) => void }} props
 */
export function GoogleSignInSection({ googleClientId, onGoogleToken }) {
  const { t } = useTranslation();
  const hostRef = useRef(/** @type {HTMLDivElement|null} */ (null));

  useEffect(() => {
    if (!googleClientId || !hostRef.current) return;
    let cancelled = false;
    const host = hostRef.current;
    host.innerHTML = "";

    renderGoogleSignInButton(host, {
      clientId: googleClientId,
      theme: "outline",
      onCredential: (token) => {
        if (!cancelled) onGoogleToken?.(token);
      },
    }).catch(() => {});

    return () => {
      cancelled = true;
      host.innerHTML = "";
    };
  }, [googleClientId, onGoogleToken]);

  if (!googleClientId) {
    if (isGoogleSignInDisabledByEnv()) return null;
    if (import.meta.env.DEV) {
      return (
        <div className="mb-6 rounded-xl border border-amber-400/25 bg-amber-500/10 px-4 py-3 text-center">
          <p className="text-xs font-medium text-amber-100/90">{t("auth.googleDevHint")}</p>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="mb-6 w-full">
      <div ref={hostRef} className="w-full min-h-[44px]" />
    </div>
  );
}

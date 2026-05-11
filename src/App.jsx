import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { AuthProviderContainer } from "./containers/AuthProviderContainer.jsx";
import { AuthScreenContainer } from "./containers/AuthScreenContainer.jsx";
import { ChatShellContainer } from "./containers/ChatShellContainer.jsx";
import { QuizContainer } from "./containers/QuizContainer.jsx";
import { useAuthContext } from "./viewmodels/AuthContext.js";
import { isGoogleSignInDisabledByEnv } from "./utils/googleSignInEnv.js";

/** Google button on login/signup. Set VITE_ENABLE_GOOGLE_SIGNIN=false to use email/phone/passkey only. */
function googleClientIdForAuthUi() {
  if (isGoogleSignInDisabledByEnv()) return null;
  const raw = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  return raw && String(raw).trim() ? String(raw).trim() : null;
}

function FullScreenLoader() {
  const { t } = useTranslation();
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-ink-900 px-6 text-center text-slate-400">
      <Loader2 className="h-7 w-7 animate-spin text-emerald-400/80" aria-hidden />
      <p className="max-w-sm text-sm leading-relaxed text-slate-500">{t("common.loadingProfile")}</p>
    </main>
  );
}

/**
 * Inner shell — split out so it can read the AuthContext that
 * `AuthProviderContainer` provides above it.
 *
 * Routing rules:
 *   1. Not authenticated      → AuthScreenContainer (login/signup)
 *   2. Authenticated, no quiz → QuizContainer (first-time onboarding)
 *   3. Authenticated, has quiz→ ChatShellContainer (wellness hub)
 *
 * The user can always re-take the quiz from the hub header. While the
 * "do they have a profile?" check is in flight we render a loader so we
 * don't briefly flash the wrong screen.
 */
function AppRoot() {
  const auth = useAuthContext();
  const [authMode] = useState(/** @type {'login'|'signup'} */ ("login"));
  const [forceQuiz, setForceQuiz] = useState(false);

  if (!auth.isAuthenticated) {
    return (
      <AuthScreenContainer
        initialMode={authMode}
        googleClientId={googleClientIdForAuthUi()}
        onAuthenticated={() => setForceQuiz(false)}
      />
    );
  }

  if (auth.isAuthenticated && !auth.profileChecked) {
    return <FullScreenLoader />;
  }

  const showQuiz = forceQuiz || !auth.hasProfile;

  if (showQuiz) {
    return (
      <QuizContainer
        onProfileSaved={(result) => {
          auth.markProfileSaved();
          if (result?.user_id) {
            // Keep the legacy localStorage path in sync so non-auth code paths
            // (analytics, the quiz reset URL flag) still see a current user.
            try {
              localStorage.setItem("holistica_user_id", String(result.user_id));
              localStorage.setItem("holistica_has_completed_onboarding", "true");
            } catch {
              /* ignore */
            }
          }
          setForceQuiz(false);
        }}
        onCancel={auth.hasProfile ? () => setForceQuiz(false) : undefined}
      />
    );
  }

  return (
    <ChatShellContainer
      userId={auth.user?.user_id}
      onRestartOnboarding={() => setForceQuiz(true)}
    />
  );
}

/**
 * Top-level composition root. Wraps everything in the AuthProvider so
 * any container can read the current authenticated user via
 * `useAuthContext()`.
 */
export default function App() {
  return (
    <AuthProviderContainer>
      <AppRoot />
    </AuthProviderContainer>
  );
}

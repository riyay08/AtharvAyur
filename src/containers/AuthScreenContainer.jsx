import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

import { isWebAuthnSupported } from "../services/webauthnService.js";
import { useAuthContext } from "../viewmodels/AuthContext.js";
import { useLoginViewModel } from "../viewmodels/useLoginViewModel.js";
import { useSignUpViewModel } from "../viewmodels/useSignUpViewModel.js";
import { AuthShellView } from "../views/AuthShellView.jsx";
import { LoginView } from "../views/LoginView.jsx";
import { SignUpView } from "../views/SignUpView.jsx";

/**
 * Composition root for the unauthenticated journey. Owns the
 * login-vs-signup toggle and forwards completed sessions back into the
 * AuthContext, then the parent (`App`) routes to the wellness hub.
 *
 * @param {{ initialMode?: 'login'|'signup', googleClientId?: string|null, onAuthenticated?: () => void }} props
 */
export function AuthScreenContainer({ initialMode = "login", googleClientId, onAuthenticated }) {
  const auth = useAuthContext();
  const [mode, setMode] = useState(initialMode);

  const handleSession = useCallback(
    (session) => {
      auth.handleSession(session);
      onAuthenticated?.(session);
    },
    [auth, onAuthenticated]
  );

  const { t } = useTranslation();
  const loginVm = useLoginViewModel({ onSession: handleSession, t });
  const signUpVm = useSignUpViewModel({ onSession: handleSession, t });

  const switchMode = useCallback(() => {
    setMode((m) => (m === "login" ? "signup" : "login"));
  }, []);

  const passkeySupported = isWebAuthnSupported();

  return (
    <AuthShellView mode={mode} onSwitchMode={switchMode}>
      {mode === "login" ? (
        <LoginView
          vm={loginVm}
          googleClientId={googleClientId || null}
          passkeySupported={passkeySupported}
          onGoogleToken={loginVm.submitGoogle}
        />
      ) : (
        <SignUpView
          vm={signUpVm}
          googleClientId={googleClientId || null}
          onGoogleToken={signUpVm.submitGoogle}
        />
      )}
    </AuthShellView>
  );
}

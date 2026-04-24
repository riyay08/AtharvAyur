/**
 * Tiny ViewModel for the "register a passkey on this device" button.
 *
 * Used by the Security panel after the user is logged in. Reuses the
 * AuthContext to update local state once a credential is successfully
 * registered.
 */

import { useCallback, useState } from "react";

import {
  isWebAuthnSupported,
  registerPasskey as registerPasskeyService,
} from "../services/webauthnService.js";

function readableErr(err, fallback) {
  if (!err) return fallback;
  if (err instanceof Error) return err.message;
  return String(err);
}

const IDENTITY = (s) => s;

/**
 * @param {{
 *   onRegistered?: () => void,
 *   t?: (key: string) => string,
 *   registerPasskey?: typeof registerPasskeyService,
 * }} [deps]
 */
export function usePasskeyViewModel(deps = {}) {
  const onRegistered = deps.onRegistered;
  const t = deps.t ?? IDENTITY;
  const registerPasskey = deps.registerPasskey ?? registerPasskeyService;

  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState(/** @type {string|null} */ (null));
  const [success, setSuccess] = useState(/** @type {string|null} */ (null));

  const supported = isWebAuthnSupported();

  const register = useCallback(
    async (label) => {
      setError(null);
      setSuccess(null);
      if (!supported) {
        setError(t("security.passkeyUnsupported"));
        return;
      }
      setRegistering(true);
      try {
        await registerPasskey({ label });
        setSuccess(t("security.passkeySuccess"));
        onRegistered?.();
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setRegistering(false);
      }
    },
    [registerPasskey, onRegistered, supported, t]
  );

  return {
    supported,
    registering,
    error,
    success,
    register,
  };
}

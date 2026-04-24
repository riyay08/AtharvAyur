/**
 * ViewModel for the login screen.
 *
 * Owns the tab (email vs phone vs passkey), the form state for each, and
 * the async submit/verify flows. Returns enough props for `LoginView` to
 * be a pure render.
 */

import { useCallback, useState } from "react";

import {
  isLikelyE164Phone,
  isLikelyEmail,
  normalizeEmail,
  normalizePhone,
} from "../models/credentialIdentifiers.js";
import {
  logInWithEmail as logInWithEmailService,
  requestPhoneOtp as requestPhoneOtpService,
  signInWithGoogle as signInWithGoogleService,
  verifyPhoneOtp as verifyPhoneOtpService,
} from "../services/authService.js";
import { logInWithPasskey as logInWithPasskeyService } from "../services/webauthnService.js";

function readableErr(err, fallback) {
  if (!err) return fallback;
  if (err instanceof Error) return err.message;
  return String(err);
}

const IDENTITY = (s) => s;

/**
 * @param {{
 *   onSession: (session: any) => void,
 *   t?: (key: string, vars?: Record<string, any>) => string,
 *   logInWithEmail?: typeof logInWithEmailService,
 *   requestPhoneOtp?: typeof requestPhoneOtpService,
 *   verifyPhoneOtp?: typeof verifyPhoneOtpService,
 *   signInWithGoogle?: typeof signInWithGoogleService,
 *   logInWithPasskey?: typeof logInWithPasskeyService,
 * }} deps
 */
export function useLoginViewModel(deps) {
  const onSession = deps.onSession;
  const t = deps.t ?? IDENTITY;
  const logInWithEmail = deps.logInWithEmail ?? logInWithEmailService;
  const requestPhoneOtp = deps.requestPhoneOtp ?? requestPhoneOtpService;
  const verifyPhoneOtp = deps.verifyPhoneOtp ?? verifyPhoneOtpService;
  const signInWithGoogle = deps.signInWithGoogle ?? signInWithGoogleService;
  const logInWithPasskey = deps.logInWithPasskey ?? logInWithPasskeyService;

  const [tab, setTab] = useState(/** @type {'email'|'phone'|'passkey'} */ ("email"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpDevCode, setOtpDevCode] = useState(/** @type {string|null} */ (null));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(/** @type {string|null} */ (null));
  const [info, setInfo] = useState(/** @type {string|null} */ (null));

  const reset = useCallback(() => {
    setError(null);
    setInfo(null);
    setSubmitting(false);
  }, []);

  const switchTab = useCallback(
    (next) => {
      setTab(next);
      reset();
    },
    [reset]
  );

  const submitEmail = useCallback(
    async (e) => {
      e?.preventDefault?.();
      reset();
      const normalized = normalizeEmail(email);
      if (!isLikelyEmail(normalized)) {
        setError(t("auth.errors.invalidEmail"));
        return;
      }
      if (!password) {
        setError(t("auth.errors.passwordRequired"));
        return;
      }
      setSubmitting(true);
      try {
        const session = await logInWithEmail({ email: normalized, password });
        onSession?.(session);
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [email, password, onSession, logInWithEmail, reset, t]
  );

  const submitPhoneRequest = useCallback(
    async (e) => {
      e?.preventDefault?.();
      reset();
      const normalized = normalizePhone(phone);
      if (!normalized) {
        setError(t("auth.errors.invalidPhone"));
        return;
      }
      setSubmitting(true);
      try {
        const out = await requestPhoneOtp({ phone: normalized });
        setOtpRequested(true);
        setOtpDevCode(out?.dev_code ?? null);
        setInfo(
          out?.dev_code
            ? t("auth.info.devCode", { code: out.dev_code })
            : t("auth.info.smsSent")
        );
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [phone, requestPhoneOtp, reset, t]
  );

  const submitPhoneVerify = useCallback(
    async (e) => {
      e?.preventDefault?.();
      reset();
      const normalized = normalizePhone(phone);
      if (!normalized || !otp) {
        setError(t("auth.errors.otpRequired"));
        return;
      }
      setSubmitting(true);
      try {
        const session = await verifyPhoneOtp({ phone: normalized, code: otp });
        onSession?.(session);
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [phone, otp, onSession, verifyPhoneOtp, reset, t]
  );

  const submitGoogle = useCallback(
    async (idToken) => {
      reset();
      if (!idToken) {
        setError(t("auth.errors.googleNoToken"));
        return;
      }
      setSubmitting(true);
      try {
        const session = await signInWithGoogle({ idToken });
        onSession?.(session);
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [onSession, signInWithGoogle, reset, t]
  );

  const submitPasskey = useCallback(async () => {
    reset();
    setSubmitting(true);
    try {
      const optionsEmail = normalizeEmail(email);
      const session = await logInWithPasskey(
        isLikelyEmail(optionsEmail) ? { email: optionsEmail } : {}
      );
      onSession?.(session);
    } catch (err) {
      setError(readableErr(err, t("common.errorGeneric")));
    } finally {
      setSubmitting(false);
    }
  }, [email, onSession, logInWithPasskey, reset, t]);

  return {
    tab,
    switchTab,
    email,
    setEmail,
    password,
    setPassword,
    phone,
    setPhone,
    otp,
    setOtp,
    otpRequested,
    otpDevCode,
    submitting,
    error,
    info,
    canSubmitEmail: isLikelyEmail(normalizeEmail(email)) && password.length > 0,
    canSubmitPhoneRequest: isLikelyE164Phone(phone),
    canSubmitPhoneVerify: isLikelyE164Phone(phone) && otp.trim().length >= 4,
    submitEmail,
    submitPhoneRequest,
    submitPhoneVerify,
    submitGoogle,
    submitPasskey,
  };
}

/**
 * ViewModel for the signup screen.
 *
 * The phone tab is just a thin wrapper around the same
 * `requestPhoneOtp`/`verifyPhoneOtp` flow as login because the backend
 * use case auto-creates a user when the OTP succeeds.
 */

import { useCallback, useState } from "react";

import {
  isLikelyE164Phone,
  isLikelyEmail,
  normalizeEmail,
  normalizePhone,
  validatePassword,
} from "../models/credentialIdentifiers.js";
import {
  requestPhoneOtp as requestPhoneOtpService,
  signInWithGoogle as signInWithGoogleService,
  signUpWithEmail as signUpWithEmailService,
  verifyPhoneOtp as verifyPhoneOtpService,
} from "../services/authService.js";

function readableErr(err, fallback) {
  if (!err) return fallback;
  if (err instanceof Error) return err.message;
  return String(err);
}

const IDENTITY = (s) => s;

const PASSWORD_ERROR_KEY = {
  required: "auth.errors.passwordRequired",
  too_short: "auth.errors.passwordTooShort",
};

/**
 * @param {{
 *   onSession: (session: any) => void,
 *   t?: (key: string, vars?: Record<string, any>) => string,
 *   signUpWithEmail?: typeof signUpWithEmailService,
 *   requestPhoneOtp?: typeof requestPhoneOtpService,
 *   verifyPhoneOtp?: typeof verifyPhoneOtpService,
 *   signInWithGoogle?: typeof signInWithGoogleService,
 * }} deps
 */
export function useSignUpViewModel(deps) {
  const onSession = deps.onSession;
  const t = deps.t ?? IDENTITY;
  const signUpWithEmail = deps.signUpWithEmail ?? signUpWithEmailService;
  const requestPhoneOtp = deps.requestPhoneOtp ?? requestPhoneOtpService;
  const verifyPhoneOtp = deps.verifyPhoneOtp ?? verifyPhoneOtpService;
  const signInWithGoogle = deps.signInWithGoogle ?? signInWithGoogleService;

  const [tab, setTab] = useState(/** @type {'email'|'phone'} */ ("email"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
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
      const pw = validatePassword(password);
      if (!pw.ok) {
        const key = PASSWORD_ERROR_KEY[pw.code] || "auth.errors.passwordRequired";
        setError(t(key));
        return;
      }
      setSubmitting(true);
      try {
        const session = await signUpWithEmail({
          email: normalized,
          password,
          displayName: displayName.trim() || undefined,
        });
        onSession?.(session);
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [email, password, displayName, signUpWithEmail, onSession, reset, t]
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
        const session = await verifyPhoneOtp({
          phone: normalized,
          code: otp,
          displayName: displayName.trim() || undefined,
        });
        onSession?.(session);
      } catch (err) {
        setError(readableErr(err, t("common.errorGeneric")));
      } finally {
        setSubmitting(false);
      }
    },
    [phone, otp, displayName, verifyPhoneOtp, onSession, reset, t]
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

  return {
    tab,
    switchTab,
    email,
    setEmail,
    password,
    setPassword,
    displayName,
    setDisplayName,
    phone,
    setPhone,
    otp,
    setOtp,
    otpRequested,
    otpDevCode,
    submitting,
    error,
    info,
    canSubmitEmail:
      isLikelyEmail(normalizeEmail(email)) && validatePassword(password).ok,
    canSubmitPhoneRequest: isLikelyE164Phone(phone),
    canSubmitPhoneVerify: isLikelyE164Phone(phone) && otp.trim().length >= 4,
    submitEmail,
    submitPhoneRequest,
    submitPhoneVerify,
    submitGoogle,
  };
}

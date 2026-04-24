/**
 * Auth service: thin wrappers around the `/auth/*` endpoints.
 *
 * Persists the access token + a small public profile in localStorage on
 * any successful login/signup so the rest of the app can read it
 * synchronously through `useAuthContext`.
 */

import { request } from "./apiClient.js";
import {
  clearStoredAuthUser,
  clearStoredAccessToken,
  clearStoredUserId,
  getStoredAuthUser,
  getStoredUserId,
  setStoredAccessToken,
  setStoredAuthUser,
  setStoredUserId,
} from "./storage.js";

function persistSession(session) {
  if (!session || typeof session !== "object") return session;
  if (session.access_token) setStoredAccessToken(session.access_token);
  if (session.user_id) setStoredUserId(String(session.user_id));
  setStoredAuthUser({
    user_id: session.user_id ?? null,
    email: session.email ?? null,
    phone: session.phone ?? null,
    display_name: session.display_name ?? null,
    primary_provider: session.primary_provider ?? null,
    email_verified: !!session.email_verified,
    phone_verified: !!session.phone_verified,
    has_password: !!session.has_password,
    has_passkey: !!session.has_passkey,
  });
  return session;
}

function maybeAttachAnonymousUser(payload) {
  const auth = getStoredAuthUser();
  if (auth && auth.user_id) return payload;
  const anon = getStoredUserId();
  if (!anon) return payload;
  return { ...payload, anonymous_user_id: anon };
}

export async function signUpWithEmail({ email, password, displayName }) {
  const body = maybeAttachAnonymousUser({
    email,
    password,
    ...(displayName ? { display_name: displayName } : {}),
  });
  const session = await request("/auth/signup/email", {
    method: "POST",
    json: body,
    auth: false,
  });
  return persistSession(session);
}

export async function logInWithEmail({ email, password }) {
  const session = await request("/auth/login/email", {
    method: "POST",
    json: { email, password },
    auth: false,
  });
  return persistSession(session);
}

export async function requestPhoneOtp({ phone }) {
  return request("/auth/phone/request-otp", {
    method: "POST",
    json: { phone },
    auth: false,
  });
}

export async function verifyPhoneOtp({ phone, code, displayName }) {
  const body = maybeAttachAnonymousUser({
    phone,
    code,
    ...(displayName ? { display_name: displayName } : {}),
  });
  const session = await request("/auth/phone/verify-otp", {
    method: "POST",
    json: body,
    auth: false,
  });
  return persistSession(session);
}

export async function signInWithGoogle({ idToken }) {
  const body = maybeAttachAnonymousUser({ id_token: idToken });
  const session = await request("/auth/google", {
    method: "POST",
    json: body,
    auth: false,
  });
  return persistSession(session);
}

export async function fetchAuthenticatedUser() {
  return request("/auth/me", { method: "GET" });
}

/**
 * Returns `true` when the signed-in user has saved a HealthProfile (i.e.
 * they have completed the dosha quiz at least once). Used to decide
 * whether to drop them into the quiz or the wellness hub after auth.
 */
export async function hasHealthProfile() {
  try {
    const me = await request("/profile/me", { method: "GET" });
    return !!me?.health_profile;
  } catch (err) {
    if (err && /** @type {any} */ (err).status === 404) return false;
    throw err;
  }
}

export function logOut() {
  clearStoredAccessToken();
  clearStoredUserId();
  clearStoredAuthUser();
}

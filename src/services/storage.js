/**
 * Small, safe wrapper around `localStorage`. Swallows errors so callers can
 * treat it as best-effort without try/catch everywhere.
 */

export const USER_STORAGE_KEY = "holistica_user_id";
export const ACCESS_TOKEN_KEY = "holistica_access_token";
export const ONBOARDING_STORAGE_KEY = "holistica_has_completed_onboarding";
export const AUTH_USER_KEY = "holistica_auth_user";

function safeGet(key) {
  try {
    return typeof localStorage !== "undefined" ? localStorage.getItem(key) : null;
  } catch {
    return null;
  }
}

function safeSet(key, value) {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

function safeRemove(key) {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

export function getStoredUserId() {
  return safeGet(USER_STORAGE_KEY);
}
export function setStoredUserId(id) {
  if (id != null) safeSet(USER_STORAGE_KEY, String(id));
}
export function clearStoredUserId() {
  safeRemove(USER_STORAGE_KEY);
}

export function getStoredAccessToken() {
  return safeGet(ACCESS_TOKEN_KEY);
}
export function setStoredAccessToken(token) {
  if (token != null) safeSet(ACCESS_TOKEN_KEY, String(token));
}
export function clearStoredAccessToken() {
  safeRemove(ACCESS_TOKEN_KEY);
}

export function getOnboardingCompleted() {
  return safeGet(ONBOARDING_STORAGE_KEY) === "true";
}
export function setOnboardingCompleted(value) {
  safeSet(ONBOARDING_STORAGE_KEY, value ? "true" : "false");
}
export function clearOnboardingCompleted() {
  safeRemove(ONBOARDING_STORAGE_KEY);
}

export function getStoredAuthUser() {
  const raw = safeGet(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === "object" && parsed != null ? parsed : null;
  } catch {
    return null;
  }
}
export function setStoredAuthUser(user) {
  if (user && typeof user === "object") {
    safeSet(AUTH_USER_KEY, JSON.stringify(user));
  } else {
    safeRemove(AUTH_USER_KEY);
  }
}
export function clearStoredAuthUser() {
  safeRemove(AUTH_USER_KEY);
}

/** Clears saved user id, JWT, and onboarding flag (e.g. to show the quiz again). */
export function clearHolisticaSession() {
  clearStoredUserId();
  clearStoredAccessToken();
  clearOnboardingCompleted();
  clearStoredAuthUser();
}

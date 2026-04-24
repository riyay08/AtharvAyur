/**
 * Pure validation/normalization helpers for the credentials a user can
 * present at the login screen. No I/O, no React.
 */

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** @param {string} value */
export function isLikelyEmail(value) {
  return typeof value === "string" && EMAIL_RE.test(value.trim());
}

/** @param {string} value */
export function normalizeEmail(value) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

const PHONE_STRIP_RE = /[\s\-().]+/g;
const PHONE_E164_RE = /^\+?[1-9]\d{7,14}$/;

/** @param {string} value */
export function normalizePhone(value) {
  if (typeof value !== "string") return "";
  const stripped = value.trim().replace(PHONE_STRIP_RE, "");
  if (!PHONE_E164_RE.test(stripped)) return "";
  return stripped.startsWith("+") ? stripped : `+${stripped}`;
}

/** @param {string} value */
export function isLikelyE164Phone(value) {
  return normalizePhone(value).length > 0;
}

const PASSWORD_MIN = 8;

/**
 * @param {string} value
 * @returns {{ ok: boolean, code: 'required' | 'too_short' | null, message: string }}
 *
 * `code` is the structured outcome that callers (ViewModels) can translate.
 * `message` keeps an English fallback for any non-React caller / legacy test.
 */
export function validatePassword(value) {
  if (typeof value !== "string" || value.length === 0) {
    return { ok: false, code: "required", message: "Enter a password." };
  }
  if (value.length < PASSWORD_MIN) {
    return {
      ok: false,
      code: "too_short",
      message: `Password must be at least ${PASSWORD_MIN} characters.`,
    };
  }
  return { ok: true, code: null, message: "" };
}

export const PASSWORD_MIN_LENGTH = PASSWORD_MIN;

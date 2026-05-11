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

/**
 * Default national dialing prefix for normalizing numbers typed without a country code.
 * Set `VITE_PHONE_DEFAULT_COUNTRY_CODE=91` (India) or `1` (US). Omit or leave empty to default to `91`
 * for this app’s primary users; set to `none` to disable localized normalization.
 */
function defaultCountryDigitsFromEnv() {
  const raw = import.meta.env.VITE_PHONE_DEFAULT_COUNTRY_CODE;
  if (raw === "none" || raw === false || raw === "false") return "";
  if (raw == null || String(raw).trim() === "") return "91";
  return String(raw).replace(/\D/g, "");
}

/**
 * @param {string} countryDigits digits only, no +
 * @param {string} stripped user input after separator strip
 * @returns {string} E.164 or "" if no localized rule matched
 */
function tryLocalizedNationalToE164(countryDigits, stripped) {
  if (!countryDigits || !stripped) return "";
  const digits = stripped.startsWith("+") ? stripped.slice(1) : stripped;

  if (countryDigits === "91") {
    if (/^[6-9]\d{9}$/.test(digits)) return `+91${digits}`;
    if (/^0[6-9]\d{9}$/.test(digits)) return `+91${digits.slice(1)}`;
    if (/^91[6-9]\d{9}$/.test(digits)) return `+${digits}`;
  }

  if (countryDigits === "1" && /^\d{10}$/.test(digits)) {
    return `+1${digits}`;
  }

  return "";
}

/** @param {string} value */
export function normalizePhone(value) {
  if (typeof value !== "string") return "";
  const stripped = value.trim().replace(PHONE_STRIP_RE, "");

  const cc = defaultCountryDigitsFromEnv();
  if (cc) {
    const localized = tryLocalizedNationalToE164(cc, stripped);
    if (localized) return localized;
  }

  const bareDigits = stripped.startsWith("+") ? stripped.slice(1) : stripped;
  // Ambiguous 10-digit Indian mobiles without a country code — reject rather than invent +987… (invalid).
  if (/^[6-9]\d{9}$/.test(bareDigits)) return "";

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

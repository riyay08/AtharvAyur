/** Set `VITE_ENABLE_GOOGLE_SIGNIN=false` (or `0`) to hide Google and use email/phone/passkey only. */
export function isGoogleSignInDisabledByEnv() {
  const v = import.meta.env.VITE_ENABLE_GOOGLE_SIGNIN;
  return v === false || v === "false" || v === "0";
}

/** “Or use email” divider: show when Google button or dev missing-client hint may appear above the tabs. */
export function showAltMethodsDivider(googleClientId) {
  return (
    Boolean(googleClientId) || (import.meta.env.DEV && !isGoogleSignInDisabledByEnv())
  );
}

/**
 * Google Identity Services loader.
 *
 * Loads the GIS script once on demand, then exposes a single
 * `requestGoogleIdToken({ clientId })` helper that resolves with the ID
 * token the user picks. The button itself is rendered by the Google
 * library via `google.accounts.id.prompt()` (One Tap) — for a button you
 * call `renderGoogleSignInButton()` and pass the host element.
 */

const GIS_SCRIPT_SRC = "https://accounts.google.com/gsi/client";
let _gisLoadPromise = null;

function loadGsi() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Google sign-in only runs in the browser."));
  }
  if (window.google?.accounts?.id) return Promise.resolve(window.google);
  if (_gisLoadPromise) return _gisLoadPromise;
  _gisLoadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GIS_SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(window.google));
      existing.addEventListener("error", () =>
        reject(new Error("Could not load Google Identity Services."))
      );
      return;
    }
    const script = document.createElement("script");
    script.src = GIS_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.addEventListener("load", () => resolve(window.google));
    script.addEventListener("error", () =>
      reject(new Error("Could not load Google Identity Services."))
    );
    document.head.appendChild(script);
  });
  return _gisLoadPromise;
}

let _initializedClientId = null;
const _pendingResolvers = [];

/** Set before each `renderButton` call; receives JWT when user uses the Google button. */
let _buttonCredentialHandler = /** @type {((credential: string) => void) | null} */ (null);

function ensureInitialized(clientId) {
  return loadGsi().then((google) => {
    if (_initializedClientId === clientId) return google;
    google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        const token = response?.credential;
        const resolver = _pendingResolvers.shift();
        if (resolver) {
          if (!token) {
            resolver.reject(new Error("Google sign-in returned no credential."));
          } else {
            resolver.resolve(token);
          }
          return;
        }
        if (token && _buttonCredentialHandler) {
          _buttonCredentialHandler(token);
        }
      },
      auto_select: false,
      cancel_on_tap_outside: true,
    });
    _initializedClientId = clientId;
    return google;
  });
}

/**
 * Render a managed Google sign-in button into `host`.
 *
 * @param {HTMLElement} host
 * @param {{ clientId: string, theme?: 'outline'|'filled_blue'|'filled_black', onCredential?: (jwt: string) => void }} opts
 * @returns {Promise<void>}
 */
export async function renderGoogleSignInButton(host, { clientId, theme = "outline", onCredential }) {
  if (!host) return;
  _buttonCredentialHandler = typeof onCredential === "function" ? onCredential : null;
  const google = await ensureInitialized(clientId);
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const w = host.getBoundingClientRect().width;
  const width = Math.min(Math.max(Math.floor(w) || 320, 200), 400);
  host.innerHTML = "";
  google.accounts.id.renderButton(host, {
    theme,
    size: "large",
    shape: "rectangular",
    text: "continue_with",
    width,
    logo_alignment: "left",
  });
}

/**
 * Programmatically trigger Google One Tap. Resolves with the ID token.
 *
 * @param {{ clientId: string }} opts
 * @returns {Promise<string>}
 */
export function requestGoogleIdToken({ clientId }) {
  return new Promise((resolve, reject) => {
    ensureInitialized(clientId)
      .then((google) => {
        _pendingResolvers.push({ resolve, reject });
        google.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed?.() || notification.isSkippedMoment?.()) {
            const r = _pendingResolvers.shift();
            r?.reject(new Error("Google sign-in was dismissed."));
          }
        });
      })
      .catch(reject);
  });
}

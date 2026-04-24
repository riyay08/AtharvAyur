/**
 * Promise-based wrapper around `navigator.geolocation.getCurrentPosition`.
 * Returns a tagged result so callers don't have to mix exceptions with data.
 *
 * @typedef {{ status: 'ok', lat: number, lon: number }} OkResult
 * @typedef {{ status: 'denied' | 'unsupported' | 'error' }} FailResult
 * @typedef {OkResult | FailResult} GeoResult
 */

/** @param {PositionOptions} [options] */
export function getCurrentPosition(options = { enableHighAccuracy: false, timeout: 15_000, maximumAge: 300_000 }) {
  return new Promise(/** @param {(v: GeoResult) => void} resolve */ (resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      resolve({ status: "unsupported" });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ status: "ok", lat: pos.coords.latitude, lon: pos.coords.longitude }),
      (err) => resolve({ status: err && err.code === 1 ? "denied" : "error" }),
      options,
    );
  });
}

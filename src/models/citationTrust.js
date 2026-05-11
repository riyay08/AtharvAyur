/**
 * Pure: classify a citation URL into a trust badge.
 * No React; safe for unit tests.
 *
 * @typedef {{ badgeClass: string, title: string, tier: 'gov_edu' | 'institutional' }} TrustMeta
 */

const INSTITUTIONAL = Object.freeze({
  badgeClass: "border-sky-400/40 bg-sky-500/12 text-sky-200",
  title: "Verified medical / institutional source",
  tier: "institutional",
});

const GOV_EDU = Object.freeze({
  badgeClass: "border-amber-400/50 bg-amber-500/15 text-amber-200",
  title: "High trust: government or academic domain",
  tier: "gov_edu",
});

/**
 * Turn API citation strings into a safe http(s) URL, or null if unusable.
 * Many models return "www.example.com" without a scheme — browsers won't navigate those.
 *
 * @param {string | undefined | null} raw
 * @returns {string | null}
 */
export function normalizeCitationHref(raw) {
  if (raw == null) return null;
  let s = String(raw).trim();
  if (!s) return null;
  if (/^javascript:/i.test(s) || /^data:/i.test(s)) return null;
  if (!/^https?:\/\//i.test(s)) {
    s = s.replace(/^\/\//, "");
    s = `https://${s}`;
  }
  try {
    const u = new URL(s);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.href;
  } catch {
    return null;
  }
}

/**
 * @param {string | undefined | null} url
 * @returns {TrustMeta}
 */
export function citationTrustMeta(url) {
  if (!url) return INSTITUTIONAL;
  try {
    const h = new URL(url).hostname.toLowerCase();
    if (h.endsWith(".gov") || h.endsWith(".edu")) return GOV_EDU;
    return INSTITUTIONAL;
  } catch {
    return INSTITUTIONAL;
  }
}

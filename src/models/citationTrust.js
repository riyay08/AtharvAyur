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

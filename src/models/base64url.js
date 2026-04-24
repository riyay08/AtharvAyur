/**
 * RFC 4648 §5 base64url helpers (no padding).
 *
 * Used by the WebAuthn flow to translate between server-issued challenges
 * (strings) and the browser's CredentialsContainer (`ArrayBuffer`).
 */

/** @param {ArrayBuffer | Uint8Array} buf */
export function arrayBufferToBase64Url(buf) {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  const b64 = typeof btoa === "function" ? btoa(binary) : Buffer.from(binary, "binary").toString("base64");
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

/** @param {string} input */
export function base64UrlToArrayBuffer(input) {
  const padded = input.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - (padded.length % 4)) % 4);
  const binary = typeof atob === "function"
    ? atob(padded + padding)
    : Buffer.from(padded + padding, "base64").toString("binary");
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

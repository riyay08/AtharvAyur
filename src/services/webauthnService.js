/**
 * WebAuthn / passkey service.
 *
 * The backend hands us PublicKeyCredentialCreationOptions /
 * RequestOptions as JSON. Browsers want `ArrayBuffer`s for `challenge`
 * and `id` fields, so this layer:
 *   1. converts those base64url fields into buffers,
 *   2. invokes `navigator.credentials.create/get`,
 *   3. converts the response back into base64url JSON,
 *   4. POSTs the result to the matching backend endpoint.
 */

import { arrayBufferToBase64Url, base64UrlToArrayBuffer } from "../models/base64url.js";
import { request } from "./apiClient.js";
import { setStoredAccessToken, setStoredAuthUser, setStoredUserId } from "./storage.js";

export function isWebAuthnSupported() {
  return (
    typeof window !== "undefined" &&
    typeof window.PublicKeyCredential === "function" &&
    !!navigator.credentials &&
    typeof navigator.credentials.create === "function" &&
    typeof navigator.credentials.get === "function"
  );
}

function decodeRegistrationOptions(options) {
  const next = { ...options };
  next.challenge = base64UrlToArrayBuffer(options.challenge);
  if (options.user?.id) {
    next.user = { ...options.user, id: base64UrlToArrayBuffer(options.user.id) };
  }
  if (Array.isArray(options.excludeCredentials)) {
    next.excludeCredentials = options.excludeCredentials.map((c) => ({
      ...c,
      id: base64UrlToArrayBuffer(c.id),
    }));
  }
  return next;
}

function decodeAuthenticationOptions(options) {
  const next = { ...options };
  next.challenge = base64UrlToArrayBuffer(options.challenge);
  if (Array.isArray(options.allowCredentials)) {
    next.allowCredentials = options.allowCredentials.map((c) => ({
      ...c,
      id: base64UrlToArrayBuffer(c.id),
    }));
  }
  return next;
}

function encodeRegistrationCredential(credential) {
  const r = credential.response;
  return {
    id: credential.id,
    rawId: arrayBufferToBase64Url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment ?? null,
    response: {
      attestationObject: arrayBufferToBase64Url(r.attestationObject),
      clientDataJSON: arrayBufferToBase64Url(r.clientDataJSON),
      transports:
        typeof r.getTransports === "function" ? r.getTransports() : undefined,
    },
    clientExtensionResults: credential.getClientExtensionResults?.() ?? {},
  };
}

function encodeAuthenticationCredential(credential) {
  const r = credential.response;
  return {
    id: credential.id,
    rawId: arrayBufferToBase64Url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment ?? null,
    response: {
      authenticatorData: arrayBufferToBase64Url(r.authenticatorData),
      clientDataJSON: arrayBufferToBase64Url(r.clientDataJSON),
      signature: arrayBufferToBase64Url(r.signature),
      userHandle: r.userHandle ? arrayBufferToBase64Url(r.userHandle) : null,
    },
    clientExtensionResults: credential.getClientExtensionResults?.() ?? {},
  };
}

/**
 * Register a new passkey for the currently signed-in user.
 * Requires an authenticated session (Bearer token in storage).
 *
 * @param {{ label?: string }} [opts]
 */
export async function registerPasskey({ label } = {}) {
  if (!isWebAuthnSupported()) {
    throw new Error("This device or browser doesn't support passkeys.");
  }
  const challenge = await request("/auth/webauthn/register/options", {
    method: "POST",
    json: {},
  });
  const options = decodeRegistrationOptions(challenge.options);
  const credential = await navigator.credentials.create({ publicKey: options });
  if (!credential) throw new Error("No passkey was returned by the browser.");
  const verified = await request("/auth/webauthn/register/verify", {
    method: "POST",
    json: {
      challenge: challenge.challenge,
      response: encodeRegistrationCredential(credential),
      ...(label ? { label } : {}),
    },
  });
  return verified;
}

/**
 * Sign in with an existing passkey.
 * Optionally pass an email to constrain which credentials are allowed.
 *
 * @param {{ email?: string }} [opts]
 */
export async function logInWithPasskey({ email } = {}) {
  if (!isWebAuthnSupported()) {
    throw new Error("This device or browser doesn't support passkeys.");
  }
  const body = email ? { email } : {};
  const challenge = await request("/auth/webauthn/login/options", {
    method: "POST",
    json: body,
    auth: false,
  });
  const options = decodeAuthenticationOptions(challenge.options);
  const credential = await navigator.credentials.get({ publicKey: options });
  if (!credential) throw new Error("No passkey was returned by the browser.");
  const session = await request("/auth/webauthn/login/verify", {
    method: "POST",
    json: {
      challenge: challenge.challenge,
      response: encodeAuthenticationCredential(credential),
    },
    auth: false,
  });
  if (session?.access_token) setStoredAccessToken(session.access_token);
  if (session?.user_id) setStoredUserId(String(session.user_id));
  setStoredAuthUser({
    user_id: session?.user_id ?? null,
    email: session?.email ?? null,
    phone: session?.phone ?? null,
    display_name: session?.display_name ?? null,
    primary_provider: session?.primary_provider ?? null,
    email_verified: !!session?.email_verified,
    phone_verified: !!session?.phone_verified,
    has_password: !!session?.has_password,
    has_passkey: !!session?.has_passkey,
  });
  return session;
}

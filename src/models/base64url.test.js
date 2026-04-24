import { describe, expect, it } from "vitest";

import { arrayBufferToBase64Url, base64UrlToArrayBuffer } from "./base64url.js";

describe("base64url", () => {
  it("round-trips arbitrary bytes", () => {
    const original = new Uint8Array([0, 1, 2, 250, 255, 128, 64, 32]);
    const encoded = arrayBufferToBase64Url(original.buffer);
    expect(encoded).not.toMatch(/[+/=]/);
    const decoded = new Uint8Array(base64UrlToArrayBuffer(encoded));
    expect(Array.from(decoded)).toEqual(Array.from(original));
  });

  it("decodes a known fixture (challenge style)", () => {
    const fixture = "AQID"; // bytes 1, 2, 3
    const decoded = new Uint8Array(base64UrlToArrayBuffer(fixture));
    expect(Array.from(decoded)).toEqual([1, 2, 3]);
  });

  it("uses url-safe alphabet on encode", () => {
    const bytes = new Uint8Array([251, 255, 191]);
    const encoded = arrayBufferToBase64Url(bytes.buffer);
    expect(encoded).toBe("-_-_");
  });
});

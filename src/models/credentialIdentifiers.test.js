import { describe, expect, it } from "vitest";

import {
  isLikelyE164Phone,
  isLikelyEmail,
  normalizeEmail,
  normalizePhone,
  validatePassword,
} from "./credentialIdentifiers.js";

describe("credentialIdentifiers", () => {
  it("normalizes and validates email addresses", () => {
    expect(isLikelyEmail("alice@example.com")).toBe(true);
    expect(isLikelyEmail("Alice@example.com")).toBe(true);
    expect(isLikelyEmail("not-an-email")).toBe(false);
    expect(isLikelyEmail("")).toBe(false);

    expect(normalizeEmail("  Alice@Example.COM  ")).toBe("alice@example.com");
    expect(normalizeEmail(undefined)).toBe("");
  });

  it("normalizes phone numbers into E.164", () => {
    expect(normalizePhone("+1 (415) 555-1234")).toBe("+14155551234");
    expect(normalizePhone("4155551234")).toBe("+4155551234");
    expect(normalizePhone("invalid")).toBe("");
    expect(isLikelyE164Phone("+14155551234")).toBe(true);
    expect(isLikelyE164Phone("123")).toBe(false);
  });

  it("enforces password length minimum", () => {
    expect(validatePassword("hunter22").ok).toBe(true);
    const short = validatePassword("short");
    expect(short.ok).toBe(false);
    expect(short.message).toMatch(/at least/);
    expect(validatePassword("").ok).toBe(false);
  });
});

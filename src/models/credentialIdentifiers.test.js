import { describe, expect, it, vi } from "vitest";

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
    vi.stubEnv("VITE_PHONE_DEFAULT_COUNTRY_CODE", "none");

    expect(normalizePhone("+1 (415) 555-1234")).toBe("+14155551234");
    expect(normalizePhone("4155551234")).toBe("+4155551234");
    expect(normalizePhone("invalid")).toBe("");
    expect(isLikelyE164Phone("+14155551234")).toBe(true);
    expect(isLikelyE164Phone("123")).toBe(false);

    vi.unstubAllEnvs();
  });

  it("defaults Indian mobiles without country code to +91 when country code env is unset", () => {
    vi.stubEnv("VITE_PHONE_DEFAULT_COUNTRY_CODE", "");

    expect(normalizePhone("9876543210")).toBe("+919876543210");
    expect(normalizePhone("09876543210")).toBe("+919876543210");
    expect(normalizePhone("919876543210")).toBe("+919876543210");
    expect(normalizePhone("+919876543210")).toBe("+919876543210");

    vi.unstubAllEnvs();
  });

  it("rejects ambiguous 10-digit Indian-looking numbers when localized rules are disabled", () => {
    vi.stubEnv("VITE_PHONE_DEFAULT_COUNTRY_CODE", "none");

    expect(normalizePhone("9876543210")).toBe("");
    expect(isLikelyE164Phone("9876543210")).toBe(false);

    vi.unstubAllEnvs();
  });

  it("normalizes US 10-digit numbers when default country is 1", () => {
    vi.stubEnv("VITE_PHONE_DEFAULT_COUNTRY_CODE", "1");

    expect(normalizePhone("4155551234")).toBe("+14155551234");

    vi.unstubAllEnvs();
  });

  it("enforces password length minimum", () => {
    expect(validatePassword("hunter22").ok).toBe(true);
    const short = validatePassword("short");
    expect(short.ok).toBe(false);
    expect(short.message).toMatch(/at least/);
    expect(validatePassword("").ok).toBe(false);
  });
});

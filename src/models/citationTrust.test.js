import { describe, expect, it } from "vitest";

import { citationTrustMeta, normalizeCitationHref } from "./citationTrust.js";

describe("citationTrustMeta", () => {
  it("tags .gov and .edu hosts as high trust", () => {
    expect(citationTrustMeta("https://www.nih.gov/studies/1").tier).toBe("gov_edu");
    expect(citationTrustMeta("https://med.stanford.edu/post").tier).toBe("gov_edu");
  });

  it("falls back to institutional for other hosts and invalid URLs", () => {
    expect(citationTrustMeta("https://example.com/a").tier).toBe("institutional");
    expect(citationTrustMeta("not a url").tier).toBe("institutional");
    expect(citationTrustMeta("").tier).toBe("institutional");
    expect(citationTrustMeta(null).tier).toBe("institutional");
  });
});

describe("normalizeCitationHref", () => {
  it("adds https for bare hostnames", () => {
    expect(normalizeCitationHref("www.nih.gov/path")).toBe("https://www.nih.gov/path");
    expect(normalizeCitationHref("example.com")).toBe("https://example.com/");
  });

  it("preserves existing schemes", () => {
    expect(normalizeCitationHref("http://a.org/x")).toBe("http://a.org/x");
    expect(normalizeCitationHref("https://b.org/y")).toBe("https://b.org/y");
  });

  it("returns null for empty or dangerous values", () => {
    expect(normalizeCitationHref("")).toBeNull();
    expect(normalizeCitationHref(null)).toBeNull();
    expect(normalizeCitationHref("javascript:alert(1)")).toBeNull();
    expect(normalizeCitationHref("data:text/html,hi")).toBeNull();
  });
});

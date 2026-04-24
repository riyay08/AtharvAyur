import { describe, expect, it } from "vitest";

import { citationTrustMeta } from "./citationTrust.js";

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

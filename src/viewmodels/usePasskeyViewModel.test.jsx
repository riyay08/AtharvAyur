import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { usePasskeyViewModel } from "./usePasskeyViewModel.js";
import { fakeT } from "./__tests__/i18nTestHelper.js";

beforeEach(() => {
  globalThis.PublicKeyCredential = class {};
  Object.defineProperty(globalThis, "navigator", {
    value: {
      credentials: {
        create: vi.fn(),
        get: vi.fn(),
      },
    },
    configurable: true,
  });
});

afterEach(() => {
  delete globalThis.PublicKeyCredential;
});

describe("usePasskeyViewModel", () => {
  it("registers a passkey and surfaces success", async () => {
    const registerPasskey = vi.fn().mockResolvedValue({});
    const onRegistered = vi.fn();
    const { result } = renderHook(() =>
      usePasskeyViewModel({ registerPasskey, onRegistered, t: fakeT })
    );

    expect(result.current.supported).toBe(true);

    await act(async () => {
      await result.current.register("Phone");
    });

    expect(registerPasskey).toHaveBeenCalledWith({ label: "Phone" });
    expect(onRegistered).toHaveBeenCalled();
    expect(result.current.success).toMatch(/Passkey registered/);
    expect(result.current.error).toBeNull();
  });

  it("surfaces errors from the underlying service", async () => {
    const registerPasskey = vi.fn().mockRejectedValue(new Error("nope"));
    const { result } = renderHook(() => usePasskeyViewModel({ registerPasskey, t: fakeT }));
    await act(async () => {
      await result.current.register();
    });
    expect(result.current.error).toBe("nope");
    expect(result.current.success).toBeNull();
  });

  it("blocks registration when WebAuthn is unsupported", async () => {
    delete globalThis.PublicKeyCredential;
    const registerPasskey = vi.fn();
    const { result } = renderHook(() => usePasskeyViewModel({ registerPasskey, t: fakeT }));
    expect(result.current.supported).toBe(false);
    await act(async () => {
      await result.current.register();
    });
    expect(registerPasskey).not.toHaveBeenCalled();
    expect(result.current.error).toMatch(/support passkeys/);
  });
});

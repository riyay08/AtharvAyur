import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useLoginViewModel } from "./useLoginViewModel.js";
import { fakeT } from "./__tests__/i18nTestHelper.js";

function setup(overrides = {}) {
  const onSession = overrides.onSession ?? vi.fn();
  const deps = {
    onSession,
    t: fakeT,
    logInWithEmail: overrides.logInWithEmail ?? vi.fn().mockResolvedValue({ access_token: "x", user_id: "u-1" }),
    requestPhoneOtp: overrides.requestPhoneOtp ?? vi.fn().mockResolvedValue({ phone: "+14155551234", dev_code: null }),
    verifyPhoneOtp: overrides.verifyPhoneOtp ?? vi.fn().mockResolvedValue({ access_token: "y", user_id: "u-2" }),
    signInWithGoogle: overrides.signInWithGoogle ?? vi.fn().mockResolvedValue({ access_token: "z", user_id: "u-3" }),
    logInWithPasskey: overrides.logInWithPasskey ?? vi.fn().mockResolvedValue({ access_token: "p", user_id: "u-4" }),
  };
  const hook = renderHook(() => useLoginViewModel(deps));
  return { ...hook, ...deps };
}

describe("useLoginViewModel", () => {
  it("rejects email login when fields are invalid", async () => {
    const { result } = setup();
    await act(async () => {
      await result.current.submitEmail();
    });
    expect(result.current.error).toMatch(/valid email/);
  });

  it("submits email login and notifies onSession on success", async () => {
    const { result, logInWithEmail, onSession } = setup();
    act(() => result.current.setEmail("alice@example.com"));
    act(() => result.current.setPassword("hunter22!"));
    expect(result.current.canSubmitEmail).toBe(true);

    await act(async () => {
      await result.current.submitEmail();
    });

    expect(logInWithEmail).toHaveBeenCalledWith({
      email: "alice@example.com",
      password: "hunter22!",
    });
    expect(onSession).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
    expect(result.current.submitting).toBe(false);
  });

  it("surfaces backend errors as readable strings", async () => {
    const { result } = setup({
      logInWithEmail: vi.fn().mockRejectedValue(new Error("Wrong password")),
    });
    act(() => result.current.setEmail("bob@example.com"));
    act(() => result.current.setPassword("anything!"));
    await act(async () => {
      await result.current.submitEmail();
    });
    expect(result.current.error).toBe("Wrong password");
  });

  it("phone flow: request OTP, then verify", async () => {
    const { result, requestPhoneOtp, verifyPhoneOtp, onSession } = setup({
      requestPhoneOtp: vi.fn().mockResolvedValue({ phone: "+14155551234", dev_code: "424242" }),
    });
    act(() => result.current.switchTab("phone"));
    act(() => result.current.setPhone("+1 (415) 555-1234"));
    expect(result.current.canSubmitPhoneRequest).toBe(true);

    await act(async () => {
      await result.current.submitPhoneRequest();
    });
    expect(requestPhoneOtp).toHaveBeenCalledWith({ phone: "+14155551234" });
    expect(result.current.otpRequested).toBe(true);
    expect(result.current.info).toMatch(/424242/);

    act(() => result.current.setOtp("424242"));
    await act(async () => {
      await result.current.submitPhoneVerify();
    });
    expect(verifyPhoneOtp).toHaveBeenCalledWith({ phone: "+14155551234", code: "424242" });
    expect(onSession).toHaveBeenCalled();
  });

  it("passkey flow defers to the WebAuthn service", async () => {
    const { result, logInWithPasskey, onSession } = setup();
    act(() => result.current.switchTab("passkey"));
    act(() => result.current.setEmail("alice@example.com"));
    await act(async () => {
      await result.current.submitPasskey();
    });
    await waitFor(() =>
      expect(logInWithPasskey).toHaveBeenCalledWith({ email: "alice@example.com" })
    );
    expect(onSession).toHaveBeenCalled();
  });

  it("google flow forwards the id token", async () => {
    const { result, signInWithGoogle, onSession } = setup();
    await act(async () => {
      await result.current.submitGoogle("g-token");
    });
    expect(signInWithGoogle).toHaveBeenCalledWith({ idToken: "g-token" });
    expect(onSession).toHaveBeenCalled();
  });
});

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useSignUpViewModel } from "./useSignUpViewModel.js";
import { fakeT } from "./__tests__/i18nTestHelper.js";

function setup(overrides = {}) {
  const deps = {
    onSession: overrides.onSession ?? vi.fn(),
    t: fakeT,
    signUpWithEmail: overrides.signUpWithEmail ?? vi.fn().mockResolvedValue({ user_id: "u-1" }),
    requestPhoneOtp: overrides.requestPhoneOtp ?? vi.fn().mockResolvedValue({ phone: "+14155551234" }),
    verifyPhoneOtp: overrides.verifyPhoneOtp ?? vi.fn().mockResolvedValue({ user_id: "u-2" }),
    signInWithGoogle: overrides.signInWithGoogle ?? vi.fn().mockResolvedValue({ user_id: "u-3" }),
  };
  const hook = renderHook(() => useSignUpViewModel(deps));
  return { ...hook, ...deps };
}

describe("useSignUpViewModel", () => {
  it("rejects short passwords before calling the service", async () => {
    const { result, signUpWithEmail } = setup();
    act(() => result.current.setEmail("alice@example.com"));
    act(() => result.current.setPassword("short"));
    await act(async () => {
      await result.current.submitEmail();
    });
    expect(signUpWithEmail).not.toHaveBeenCalled();
    expect(result.current.error).toMatch(/at least/);
  });

  it("creates an account when the form is valid", async () => {
    const { result, signUpWithEmail, onSession } = setup();
    act(() => result.current.setEmail("alice@example.com"));
    act(() => result.current.setPassword("hunter22!"));
    act(() => result.current.setDisplayName("Alice"));
    expect(result.current.canSubmitEmail).toBe(true);

    await act(async () => {
      await result.current.submitEmail();
    });
    expect(signUpWithEmail).toHaveBeenCalledWith({
      email: "alice@example.com",
      password: "hunter22!",
      displayName: "Alice",
    });
    expect(onSession).toHaveBeenCalled();
  });

  it("phone flow walks request -> verify and forwards display name", async () => {
    const { result, requestPhoneOtp, verifyPhoneOtp, onSession } = setup();
    act(() => result.current.switchTab("phone"));
    act(() => result.current.setPhone("+14155551234"));
    act(() => result.current.setDisplayName("Bob"));
    await act(async () => {
      await result.current.submitPhoneRequest();
    });
    expect(requestPhoneOtp).toHaveBeenCalledWith({ phone: "+14155551234" });

    act(() => result.current.setOtp("424242"));
    await act(async () => {
      await result.current.submitPhoneVerify();
    });
    expect(verifyPhoneOtp).toHaveBeenCalledWith({
      phone: "+14155551234",
      code: "424242",
      displayName: "Bob",
    });
    expect(onSession).toHaveBeenCalled();
  });
});

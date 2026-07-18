import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useHealthChatViewModel } from "./useHealthChatViewModel.js";

describe("useHealthChatViewModel", () => {
  it("appends user + assistant messages and attaches citations", async () => {
    const sendChatMessage = vi.fn().mockResolvedValue({
      conversation_id: "conv-1",
      response_text: "Drink warm water.",
      citations: [{ url: "https://example.com", source_name: "Example" }],
      web_search_queries: ["hydration"],
    });
    const { result } = renderHook(() =>
      useHealthChatViewModel({ userId: "u-1", sendChatMessage })
    );

    act(() => result.current.setInput("how to hydrate?"));
    await act(async () => {
      await result.current.send();
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0]).toMatchObject({ role: "user", text: "how to hydrate?" });
    expect(result.current.messages[1]).toMatchObject({
      role: "assistant",
      text: "Drink warm water.",
      webSearchQueries: ["hydration"],
    });
    expect(result.current.messages[1].citations).toHaveLength(1);
    expect(result.current.input).toBe("");
    expect(result.current.loading).toBe(false);
  });

  it("marks replies as blocked when the server refuses", async () => {
    const sendChatMessage = vi.fn().mockResolvedValue({
      blocked: true,
      response_text: "Can't help with that.",
      safety_reason: "crisis",
      matched_terms: ["suicide"],
    });
    const { result } = renderHook(() =>
      useHealthChatViewModel({ userId: "u-1", sendChatMessage })
    );

    act(() => result.current.setInput("trigger"));
    await act(async () => {
      await result.current.send();
    });

    expect(result.current.messages[1]).toMatchObject({
      role: "assistant",
      blocked: true,
      safetyReason: "crisis",
      matchedTerms: ["suicide"],
    });
  });

  it("restores the input and removes the user bubble on failure", async () => {
    const sendChatMessage = vi.fn().mockRejectedValue(new Error("down"));
    const { result } = renderHook(() =>
      useHealthChatViewModel({ userId: "u-1", sendChatMessage })
    );

    act(() => result.current.setInput("hello"));
    await act(async () => {
      await result.current.send();
    });

    expect(result.current.error).toBe("down");
    expect(result.current.messages).toEqual([]);
    expect(result.current.input).toBe("hello");
  });

  it("does nothing without a user id", async () => {
    const sendChatMessage = vi.fn();
    const { result } = renderHook(() =>
      useHealthChatViewModel({ userId: null, sendChatMessage })
    );
    act(() => result.current.setInput("hi"));
    await act(async () => {
      await result.current.send();
    });
    expect(sendChatMessage).not.toHaveBeenCalled();
  });

  it("schedules endSession when the chat panel unmounts", async () => {
    const endSession = vi.fn().mockResolvedValue({ summary_pending: true });
    const { unmount } = renderHook(() =>
      useHealthChatViewModel({ userId: "u-1", sendChatMessage: vi.fn(), endSession })
    );

    unmount();

    await waitFor(() => {
      expect(endSession).toHaveBeenCalledTimes(1);
    });
  });
});

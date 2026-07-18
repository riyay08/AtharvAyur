import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
  ensureSession: vi.fn().mockResolvedValue(undefined),
  getStoredUserId: vi.fn(() => "user-1"),
  getStoredConversationId: vi.fn(() => null),
  setStoredConversationId: vi.fn(),
  clearStoredConversationId: vi.fn(),
}));

vi.mock("./apiClient.js", () => ({ request: mocks.request }));
vi.mock("./sessionService.js", () => ({ ensureSession: mocks.ensureSession }));
vi.mock("./storage.js", () => ({
  getStoredUserId: mocks.getStoredUserId,
  getStoredConversationId: mocks.getStoredConversationId,
  setStoredConversationId: mocks.setStoredConversationId,
  clearStoredConversationId: mocks.clearStoredConversationId,
}));

import {
  CHAT_TURN_PATH,
  clearActiveConversationId,
  endSession,
  sendChatMessage,
} from "./chatService.js";

describe("chatService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getStoredUserId.mockReturnValue("user-1");
    mocks.getStoredConversationId.mockReturnValue(null);
    mocks.ensureSession.mockResolvedValue(undefined);
  });

  it("posts to /api/v1/chat and stores conversation_id from the response", async () => {
    mocks.request.mockResolvedValueOnce({
      conversation_id: "conv-1",
      response_text: "Hello",
      blocked: false,
    });

    const data = await sendChatMessage("Hi");

    expect(mocks.ensureSession).toHaveBeenCalled();
    expect(mocks.request).toHaveBeenCalledWith(CHAT_TURN_PATH, {
      method: "POST",
      json: { message: "Hi" },
    });
    expect(mocks.setStoredConversationId).toHaveBeenCalledWith("user-1", "conv-1");
    expect(data.conversation_id).toBe("conv-1");
  });

  it("includes conversation_id in the JSON body on follow-up turns", async () => {
    mocks.getStoredConversationId.mockReturnValue("conv-1");
    mocks.request.mockResolvedValueOnce({
      conversation_id: "conv-1",
      response_text: "Follow-up",
      blocked: false,
    });

    await sendChatMessage("Again", { latitude: 1, longitude: 2 });

    expect(mocks.request).toHaveBeenCalledWith(CHAT_TURN_PATH, {
      method: "POST",
      json: {
        message: "Again",
        conversation_id: "conv-1",
        latitude: 1,
        longitude: 2,
      },
    });
  });

  it("clears stale conversation_id and retries once after a 404", async () => {
    mocks.getStoredConversationId.mockReturnValue("stale-conv");
    const notFound = new Error("not found");
    notFound.status = 404;
    mocks.request
      .mockRejectedValueOnce(notFound)
      .mockResolvedValueOnce({
        conversation_id: "fresh-conv",
        response_text: "Recovered",
        blocked: false,
      });

    const data = await sendChatMessage("Hello");

    expect(mocks.clearStoredConversationId).toHaveBeenCalledWith("user-1");
    expect(mocks.request).toHaveBeenCalledTimes(2);
    expect(mocks.request.mock.calls[1][1].json).toEqual({ message: "Hello" });
    expect(mocks.setStoredConversationId).toHaveBeenCalledWith("user-1", "fresh-conv");
    expect(data.conversation_id).toBe("fresh-conv");
  });

  it("endSession posts to the Janitor endpoint and clears storage", async () => {
    mocks.getStoredConversationId.mockReturnValue("conv-9");
    mocks.request.mockResolvedValueOnce({
      conversation_id: "conv-9",
      status: "ended",
      summary_pending: true,
    });

    const data = await endSession();

    expect(mocks.request).toHaveBeenCalledWith("/api/v1/conversations/conv-9/end", {
      method: "POST",
    });
    expect(mocks.clearStoredConversationId).toHaveBeenCalledWith("user-1");
    expect(data?.summary_pending).toBe(true);
  });

  it("clearActiveConversationId removes the stored id without calling the API", () => {
    clearActiveConversationId();
    expect(mocks.clearStoredConversationId).toHaveBeenCalledWith("user-1");
    expect(mocks.request).not.toHaveBeenCalled();
  });
});

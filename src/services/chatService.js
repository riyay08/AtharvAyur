import { request } from "./apiClient.js";
import { ensureSession } from "./sessionService.js";
import {
  clearStoredConversationId,
  getStoredConversationId,
  getStoredUserId,
  setStoredConversationId,
} from "./storage.js";

/** v2 orchestrated chat turn (memory pipeline + session persistence). */
export const CHAT_TURN_PATH = "/api/v1/chat";

/**
 * @deprecated Legacy endpoint — superseded by {@link CHAT_TURN_PATH}. Kept only
 * as a reference while older docs/clients migrate; do not call from app code.
 */
export const LEGACY_CHAT_PATH = "/chat";

/**
 * @returns {string | null}
 */
export function getActiveConversationId() {
  return getStoredConversationId(getStoredUserId());
}

/**
 * @param {string | null | undefined} conversationId
 */
export function setActiveConversationId(conversationId) {
  const userId = getStoredUserId();
  if (!userId) return;
  if (conversationId) {
    setStoredConversationId(userId, conversationId);
  } else {
    clearStoredConversationId(userId);
  }
}

/** Drop the in-memory session id (e.g. after Janitor runs). Does not call the API. */
export function clearActiveConversationId() {
  clearStoredConversationId(getStoredUserId());
}

/**
 * @param {string} message
 * @param {{ latitude?: number, longitude?: number, conversationId?: string | null } | undefined} options
 */
export async function sendChatMessage(message, options) {
  await ensureSession();

  const coords =
    options && typeof options === "object" && !Array.isArray(options) ? options : undefined;
  const latitude = coords?.latitude;
  const longitude = coords?.longitude;
  const explicitConversationId =
    coords && "conversationId" in coords ? coords.conversationId : undefined;

  let conversationId =
    explicitConversationId !== undefined ? explicitConversationId : getActiveConversationId();

  /** @type {Record<string, unknown>} */
  const buildBody = (convId) => {
    const body = { message };
    if (convId) body.conversation_id = convId;
    if (typeof latitude === "number" && typeof longitude === "number") {
      body.latitude = latitude;
      body.longitude = longitude;
    }
    return body;
  };

  try {
    const data = await postChatTurn(buildBody(conversationId));
    if (data?.conversation_id) {
      setActiveConversationId(data.conversation_id);
    }
    return data;
  } catch (e) {
    const status = e && typeof e === "object" && "status" in e ? e.status : undefined;
    if (status === 404 && conversationId) {
      clearActiveConversationId();
      const data = await postChatTurn(buildBody(null));
      if (data?.conversation_id) {
        setActiveConversationId(data.conversation_id);
      }
      return data;
    }
    throw e;
  }
}

/**
 * End the current (or given) conversation and schedule the Janitor summarizer.
 * Clears the stored conversation id on success or 404 (stale id).
 *
 * @param {string | null | undefined} [conversationId]
 * @returns {Promise<{ conversation_id: string, status: string, summary_pending: boolean } | null>}
 */
export async function endSession(conversationId) {
  const id = conversationId ?? getActiveConversationId();
  if (!id) return null;

  await ensureSession();

  try {
    const data = await request(
      `/api/v1/conversations/${encodeURIComponent(id)}/end`,
      { method: "POST" }
    );
    clearActiveConversationId();
    return data;
  } catch (e) {
    const status = e && typeof e === "object" && "status" in e ? e.status : undefined;
    if (status === 404) {
      clearActiveConversationId();
      return null;
    }
    throw e;
  }
}

/**
 * End any active session and start fresh on the next message.
 * @returns {Promise<void>}
 */
export async function startNewChatSession() {
  try {
    await endSession();
  } catch {
    clearActiveConversationId();
  }
}

async function postChatTurn(body) {
  return request(CHAT_TURN_PATH, { method: "POST", json: body });
}

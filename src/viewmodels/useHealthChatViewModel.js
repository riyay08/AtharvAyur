import { useCallback, useEffect, useState } from "react";

import {
  endSession as endSessionApi,
  sendChatMessage as sendChatMessageApi,
} from "../services/chatService.js";

/**
 * ViewModel for the chat panel.
 *
 * @param {{
 *   userId: string | null,
 *   latitude?: number | null,
 *   longitude?: number | null,
 *   sendChatMessage?: typeof sendChatMessageApi,
 *   endSession?: typeof endSessionApi,
 * }} params
 */
export function useHealthChatViewModel({
  userId,
  latitude,
  longitude,
  sendChatMessage = sendChatMessageApi,
  endSession = endSessionApi,
}) {
  const [messages, setMessages] = useState(/** @type {any[]} */ ([]));
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(/** @type {string | null} */ (null));

  useEffect(() => {
    return () => {
      void endSession().catch(() => {
        /* Janitor scheduling is best-effort when leaving the chat panel */
      });
    };
  }, [endSession]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || !userId || loading) return;
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const options =
        typeof latitude === "number" && typeof longitude === "number"
          ? { latitude, longitude }
          : undefined;
      const data = await sendChatMessage(text, options);
      const assistantMsg = data.blocked
        ? {
            role: "assistant",
            text:
              data.response_text ||
              data.reply ||
              "This message could not be processed.",
            blocked: true,
            safetyReason: data.safety_reason,
            matchedTerms: data.matched_terms,
          }
        : {
            role: "assistant",
            text: data.response_text || data.reply || "",
            citations: data.citations || [],
            webSearchQueries: data.web_search_queries || [],
            modelSafety: data.blocked_by_model_safety,
          };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
      setMessages((m) => m.slice(0, -1));
      setInput(text);
    } finally {
      setLoading(false);
    }
  }, [input, userId, loading, latitude, longitude, sendChatMessage]);

  return {
    messages,
    input,
    loading,
    error,
    setInput,
    send,
  };
}

import { useCallback, useState } from "react";

import {
  clearHolisticaSession,
  getOnboardingCompleted,
  getStoredUserId,
  setOnboardingCompleted,
  setStoredUserId,
} from "../services/storage.js";

/** One-shot per page load. */
let quizResetFromUrlConsumed = false;

function consumeQuizResetFromUrl() {
  if (quizResetFromUrlConsumed || typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  const wantsReset = params.has("reset") || params.get("quiz") === "1";
  if (!wantsReset) return false;
  quizResetFromUrlConsumed = true;
  clearHolisticaSession();
  const path = window.location.pathname || "/";
  window.history.replaceState({}, "", path);
  return true;
}

/**
 * ViewModel for the top-level app shell. Owns routing between 'quiz' and
 * 'chat' and the stored user id.
 */
export function useAppShellViewModel() {
  const [backendUserId, setBackendUserId] = useState(() => {
    const forced = consumeQuizResetFromUrl();
    return forced ? null : getStoredUserId();
  });
  const [screen, setScreen] = useState(() => {
    consumeQuizResetFromUrl();
    const hasDone = getOnboardingCompleted();
    const storedUserId = getStoredUserId();
    return hasDone && storedUserId ? "chat" : "quiz";
  });

  const completeOnboarding = useCallback((result) => {
    if (result?.user_id) {
      setStoredUserId(result.user_id);
      setBackendUserId(result.user_id);
    }
    setOnboardingCompleted(true);
    setScreen("chat");
  }, []);

  const restartOnboarding = useCallback(() => {
    clearHolisticaSession();
    setBackendUserId(null);
    setScreen("quiz");
  }, []);

  return { backendUserId, screen, completeOnboarding, restartOnboarding };
}

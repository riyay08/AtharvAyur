import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DOSHA_MAP, QUIZ_QUESTIONS } from "../data/quizData.js";
import { buildAssessment, progressPercent } from "../models/quizScoring.js";
import { buildProfilePayload } from "../models/profilePayload.js";
import { upsertProfile as upsertProfileApi } from "../services/profileService.js";
import { setStoredUserId } from "../services/storage.js";

const DEFAULT_AUTO_ADVANCE_MS = 280;

const IDENTITY = (s) => s;

/**
 * ViewModel for the onboarding quiz + results screens.
 *
 * @param {{
 *   questions?: typeof QUIZ_QUESTIONS,
 *   doshaMap?: typeof DOSHA_MAP,
 *   upsertProfile?: (payload: object) => Promise<any>,
 *   onProfileSaved?: (result: { user_id?: string }) => void,
 *   autoAdvanceMs?: number,
 *   t?: (key: string) => string,
 * }} [deps]
 */
export function useQuizViewModel(deps = {}) {
  const questions = deps.questions ?? QUIZ_QUESTIONS;
  const doshaMap = deps.doshaMap ?? DOSHA_MAP;
  const upsertProfile = deps.upsertProfile ?? upsertProfileApi;
  const autoAdvanceMs = deps.autoAdvanceMs ?? DEFAULT_AUTO_ADVANCE_MS;
  const t = deps.t ?? IDENTITY;

  const [route, setRoute] = useState(/** @type {'quiz'|'results'} */ ("quiz"));
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState(/** @type {Record<string,string>} */ ({}));
  const [assessment, setAssessment] = useState(
    /** @type {ReturnType<typeof buildAssessment> | null} */ (null)
  );
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(/** @type {string | null} */ (null));

  const currentQuestion = questions[questionIndex];
  const selectedKey = currentQuestion ? answers[currentQuestion.id] : undefined;
  const isLastQuestion = questionIndex === questions.length - 1;
  const canGoNext = Boolean(selectedKey);
  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const progress = useMemo(
    () => progressPercent(answeredCount, questions.length),
    [answeredCount, questions.length]
  );

  const advanceTimerRef = useRef(/** @type {ReturnType<typeof setTimeout>|null} */ (null));
  const cancelPendingAdvance = useCallback(() => {
    if (advanceTimerRef.current != null) {
      clearTimeout(advanceTimerRef.current);
      advanceTimerRef.current = null;
    }
  }, []);

  useEffect(() => cancelPendingAdvance, [cancelPendingAdvance]);

  const selectAnswer = useCallback(
    (key) => {
      if (!currentQuestion) return;
      cancelPendingAdvance();
      setAnswers((prev) => ({ ...prev, [currentQuestion.id]: key }));
      if (autoAdvanceMs > 0) {
        const questionId = currentQuestion.id;
        const wasLast = isLastQuestion;
        const lastIdx = questions.length - 1;
        advanceTimerRef.current = setTimeout(() => {
          advanceTimerRef.current = null;
          setAnswers((prev) => {
            // Bail out if the user changed their mind / went back before the timer fired.
            if (prev[questionId] !== key) return prev;
            if (wasLast) {
              setAssessment(buildAssessment(questions, prev, doshaMap));
              setRoute("results");
            } else {
              setQuestionIndex((idx) => (idx === lastIdx ? idx : idx + 1));
            }
            return prev;
          });
        }, autoAdvanceMs);
      }
    },
    [
      currentQuestion,
      cancelPendingAdvance,
      autoAdvanceMs,
      isLastQuestion,
      questions,
      doshaMap,
    ]
  );

  const goNext = useCallback(() => {
    if (!canGoNext) return;
    cancelPendingAdvance();
    if (isLastQuestion) {
      setAssessment(buildAssessment(questions, answers, doshaMap));
      setRoute("results");
      return;
    }
    setQuestionIndex((prev) => prev + 1);
  }, [answers, canGoNext, cancelPendingAdvance, doshaMap, isLastQuestion, questions]);

  const skipQuestion = useCallback(() => {
    cancelPendingAdvance();
    if (isLastQuestion) {
      setAssessment(buildAssessment(questions, answers, doshaMap));
      setRoute("results");
      return;
    }
    setQuestionIndex((prev) => Math.min(prev + 1, questions.length - 1));
  }, [answers, cancelPendingAdvance, doshaMap, isLastQuestion, questions]);

  const goBack = useCallback(() => {
    cancelPendingAdvance();
    setQuestionIndex((prev) => Math.max(0, prev - 1));
  }, [cancelPendingAdvance]);

  const reset = useCallback(() => {
    cancelPendingAdvance();
    setRoute("quiz");
    setQuestionIndex(0);
    setAnswers({});
    setAssessment(null);
    setSubmitError(null);
    setSubmitting(false);
  }, [cancelPendingAdvance]);

  const submitProfile = useCallback(async () => {
    if (!assessment) return;
    setSubmitError(null);
    setSubmitting(true);
    try {
      const payload = buildProfilePayload(assessment, answers, questions);
      const result = await upsertProfile(payload);
      if (result?.user_id) setStoredUserId(result.user_id);
      deps.onProfileSaved?.(result);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : t("quiz.couldNotSave")
      );
    } finally {
      setSubmitting(false);
    }
  }, [assessment, answers, questions, upsertProfile, deps, t]);

  /**
   * "Skip the rest" — persists whatever the user has answered so far
   * (or an empty placeholder) under a `skipped: true` consent flag and
   * resolves like a normal completion. The user won't be re-prompted to
   * fill the quiz on next login; they can still update it from the hub.
   */
  const skipAssessment = useCallback(async () => {
    setSubmitError(null);
    setSubmitting(true);
    try {
      const partialAssessment = assessment || buildAssessment(questions, answers, doshaMap);
      const payload = buildProfilePayload(partialAssessment, answers, questions);
      payload.consent_flags = {
        ...(payload.consent_flags || {}),
        prakriti_quiz_completed: false,
        prakriti_quiz_skipped: true,
      };
      const result = await upsertProfile(payload);
      if (result?.user_id) setStoredUserId(result.user_id);
      deps.onProfileSaved?.(result);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : t("quiz.couldNotSkip")
      );
    } finally {
      setSubmitting(false);
    }
  }, [answers, assessment, deps, doshaMap, questions, upsertProfile, t]);

  return {
    route,
    questionIndex,
    currentQuestion,
    selectedKey,
    answers,
    assessment,
    progress,
    isLastQuestion,
    canGoNext,
    submitting,
    submitError,
    selectAnswer,
    goNext,
    goBack,
    skipQuestion,
    reset,
    submitProfile,
    skipAssessment,
  };
}

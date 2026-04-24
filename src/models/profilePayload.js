/**
 * Pure: build the request payload for `POST /profile` from a quiz Assessment.
 * No I/O, no side effects.
 */

/**
 * @param {import('./quizScoring.js').Assessment} assessment
 * @param {Record<string,string>} answers - questionId -> option key
 * @param {import('./quizScoring.js').QuizQuestion[]} questions
 * @param {{ app?: string, completedAt?: string }} [opts]
 */
export function buildProfilePayload(assessment, answers, questions, opts = {}) {
  const selectedAnswers = questions.map((q) => ({
    question_id: q.id,
    question_text: q.prompt,
    selected_option_key: answers[q.id] || null,
    selected_option_text: answers[q.id] ? q.options[answers[q.id]] ?? null : null,
  }));

  return {
    consent_flags: {
      prakriti_quiz_completed: true,
      app: opts.app ?? "holistica_web",
    },
    prakriti_quiz: {
      dominant_dosha: assessment.dominantDosha,
      dosha_distribution: assessment.scores,
      raw_quiz_data: assessment.rawQuizData,
      selected_answers: selectedAnswers,
      completed_at: opts.completedAt ?? new Date().toISOString(),
    },
  };
}

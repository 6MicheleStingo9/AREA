import type { Answer, AnswerError, FollowUp, Question } from './types';

/*
 * The rules of the questionnaire, as quiz/logic.py applies them on the server: which follow-ups an
 * answer opens, and what is missing in it. tests/fixtures/questionnaire_cases.json holds the cases
 * that both must satisfy (logic.test.ts here, tests/test_quiz_logic.py there).
 */

/** The options chosen, as indices: one for a multiple choice, any number for a checkbox */
function chosen(question: Question, answer: Answer): number[] {
  if (question.type === 'multiple_choice') {
    return answer.choice === undefined || answer.choice === null ? [] : [answer.choice];
  }
  if (question.type === 'checkbox') {
    return [...new Set(answer.choices ?? [])].sort((a, b) => a - b);
  }
  return [];
}

const otherText = (answer: Answer) => (answer.other ?? '').trim();

function opens(followup: FollowUp, question: Question, answer: Answer): boolean {
  const { type, value } = followup.condition;
  const options = chosen(question, answer);
  switch (type) {
    case 'always':
      // From the start for a written answer; for the others, once there is a choice
      return question.type === 'free_text' || options.length > 0 || otherText(answer) !== '';
    case 'option_index':
      return question.type === 'multiple_choice' && options.includes(value as number);
    case 'option_index_in':
      return options.some((index) => ((value as number[] | undefined) ?? []).includes(index));
    default:
      return false;
  }
}

/** The indices of the follow-ups that the answer opens */
export function visibleFollowups(question: Question, answer: Answer = {}): number[] {
  return question.follow_ups.flatMap((followup, index) =>
    opens(followup, question, answer) ? [index] : [],
  );
}

/** What is missing or wrong in the answer to a question: none when it is complete */
export function answerErrors(question: Question, answer?: Answer | null): AnswerError[] {
  const given = answer ?? {};
  const errors: AnswerError[] = [];
  const required = question.required ?? false;
  if (question.type === 'free_text') {
    const text = (given.text ?? '').trim();
    const { min_length: least = 0, max_length: most } = question.validation ?? {};
    if (!text) {
      if (required) errors.push({ code: 'required' });
    } else if (text.length < least) {
      errors.push({ code: 'min_length', min: least });
    } else if (most !== undefined && text.length > most) {
      errors.push({ code: 'max_length', max: most });
    }
  } else {
    const count = question.options?.length ?? 0;
    const options = chosen(question, given);
    if (options.some((index) => index < 0 || index >= count)) {
      errors.push({ code: 'unknown_option' });
    } else if (question.type === 'multiple_choice') {
      if (required && options.length === 0) errors.push({ code: 'required' });
    } else if (given.other !== undefined && given.other !== null && !otherText(given)) {
      // "Other" ticked: it needs its text, however many options are chosen besides
      errors.push({ code: 'other_required' });
    } else {
      const least = required ? (question.min_selections ?? 1) : 0;
      if (options.length + (otherText(given) ? 1 : 0) < least) {
        errors.push({ code: 'min_selections', min: least });
      }
    }
  }
  for (const index of visibleFollowups(question, given)) {
    const text = given.followups?.[String(index)] ?? '';
    if (question.follow_ups[index]?.required && !text.trim()) {
      errors.push({ code: 'followup_required', followup: index });
    }
  }
  return errors;
}

export function isComplete(question: Question, answer?: Answer | null): boolean {
  return answerErrors(question, answer).length === 0;
}

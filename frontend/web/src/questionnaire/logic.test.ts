import { describe, expect, it } from 'vitest';
import cases from '../../../../tests/fixtures/questionnaire_cases.json';
import { answerErrors, visibleFollowups } from './logic';
import type { Answer, Question } from './types';

// The cases are the same that tests/test_quiz_logic.py runs on quiz/logic.py
const asQuestion = (question: object) => ({ follow_ups: [], ...question }) as unknown as Question;

describe('the follow-ups that an answer opens', () => {
  it.each(cases.followups.map((c) => [c.name, c] as const))('%s', (_, c) => {
    expect(visibleFollowups(asQuestion(c.question), c.answer as Answer)).toEqual(c.visible);
  });
});

describe('the checks on an answer', () => {
  it.each(cases.validation.map((c) => [c.name, c] as const))('%s', (_, c) => {
    expect(answerErrors(asQuestion(c.question), c.answer as Answer | null)).toEqual(c.errors);
  });
});

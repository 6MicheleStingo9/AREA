import type { Question } from './types';

/** The questions by MIT domain, in their order: the domain is the first part of the id ("1" of "1.3") */
export function byDomain(questions: Question[]): { domain: string; questions: Question[] }[] {
  const domains = new Map<string, Question[]>();
  for (const question of questions) {
    const domain = question.id.split('.')[0] ?? question.id;
    domains.set(domain, [...(domains.get(domain) ?? []), question]);
  }
  return [...domains].map(([domain, list]) => ({ domain, questions: list }));
}

import { useWebI18n } from '../messages';
import type { AnswerError } from './types';

/** The sentence that explains an error of an answer, in the language of the interface */
export function useErrorText(): (error: AnswerError) => string {
  const { t } = useWebI18n();
  return (error) => {
    switch (error.code) {
      case 'min_length':
        return t('app.question.errors.min_length', { min: error.min ?? 0 });
      case 'max_length':
        return t('app.question.errors.max_length', { max: error.max ?? 0 });
      case 'min_selections':
        return t('app.question.errors.min_selections', { count: error.min ?? 1 });
      default:
        return t(`app.question.errors.${error.code}`);
    }
  };
}

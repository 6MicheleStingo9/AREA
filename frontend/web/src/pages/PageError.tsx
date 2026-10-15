import { Button, Heading } from '@kindynos/ui';
import { RotateCw } from 'lucide-react';
import { useWebI18n } from '../messages';
import { useDocumentTitle } from '../pageTitle';
import page from './Page.module.css';

/** A page that could not draw itself: the questionnaire did not load, most likely */
export function PageError() {
  const { t } = useWebI18n();
  useDocumentTitle(t('app.page_title', { page: t('app.load_error.title') }));
  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <Heading level={1}>{t('app.load_error.title')}</Heading>
        <p className={page.lead}>{t('app.load_error.text')}</p>
      </div>
      <div className={page.actions}>
        <Button icon={<RotateCw />} onClick={() => window.location.reload()}>
          {t('app.load_error.retry')}
        </Button>
      </div>
    </div>
  );
}

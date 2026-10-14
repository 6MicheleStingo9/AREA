import { ButtonLink } from '@kindynos/ui';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router';
import { useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import page from './Page.module.css';

export function NotFound() {
  const { t } = useWebI18n();
  useDocumentTitle(t('app.page_title', { page: t('app.not_found.page_title') }));
  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <PageHeading>{t('app.not_found.title')}</PageHeading>
        <p className={page.lead}>{t('app.not_found.text')}</p>
      </div>
      <div className={page.actions}>
        <ButtonLink as={Link} to="/" variant="secondary" icon={<ArrowLeft />}>
          {t('app.not_found.home')}
        </ButtonLink>
      </div>
    </div>
  );
}

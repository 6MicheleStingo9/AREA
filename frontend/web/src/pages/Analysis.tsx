import { ButtonLink, Eyebrow } from '@kindynos/ui';
import { ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router';
import type { AssessmentStatus } from '../api';
import { useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import page from './Page.module.css';
import { Progress } from './Progress';
import { Result } from './Result';
import { useAssessmentStatus } from './useAssessmentStatus';

/** An analysis at /analysis/<id>: its progress while it runs, then its results */
export function Analysis() {
  const { runId = '' } = useParams();
  return <AnalysisScreen key={runId} runId={runId} />;
}

function AnalysisScreen({ runId }: { runId: string }) {
  const { t } = useWebI18n();
  const { status, offline } = useAssessmentStatus(runId);
  if (!status) {
    return (
      <div className={`${page.page} ${page.narrow}`}>
        <p className={page.note}>{t('app.loading')}</p>
      </div>
    );
  }
  switch (status.status) {
    case 'done':
      return <Result status={status} />;
    case 'error':
    case 'interrupted':
      return <Stopped status={status} />;
    case 'not_found':
      return <Missing />;
    default:
      return <Progress status={status} offline={offline} />;
  }
}

/** An analysis that stopped: the reason, the details, and the way back to the answers */
function Stopped({ status }: { status: AssessmentStatus }) {
  const { t } = useWebI18n();
  const interrupted = status.status === 'interrupted';
  const title = interrupted ? t('app.analysis.interrupted_title') : t('app.analysis.error_title');
  useDocumentTitle(t('app.page_title', { page: title }));
  let text = t('app.analysis.error_failed');
  if (interrupted) text = t('app.analysis.interrupted_text');
  else if (status.error_code === 'quota') text = t('app.analysis.error_quota');
  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <Eyebrow>{t('app.analysis.eyebrow')}</Eyebrow>
        <PageHeading>{title}</PageHeading>
        <p className={page.lead}>{text}</p>
      </div>
      {status.error && (
        <details className={page.details}>
          <summary>{t('app.analysis.error_details')}</summary>
          <pre>{status.error}</pre>
        </details>
      )}
      <div className={page.actions}>
        <ButtonLink as={Link} to="/review" icon={<ArrowLeft />}>
          {t('app.analysis.back_to_answers')}
        </ButtonLink>
      </div>
    </div>
  );
}

function Missing() {
  const { t } = useWebI18n();
  useDocumentTitle(t('app.page_title', { page: t('app.analysis.not_found_title') }));
  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <PageHeading>{t('app.analysis.not_found_title')}</PageHeading>
        <p className={page.lead}>{t('app.analysis.not_found_text')}</p>
      </div>
      <div className={page.actions}>
        <ButtonLink as={Link} to="/" variant="secondary" icon={<ArrowLeft />}>
          {t('app.not_found.home')}
        </ButtonLink>
      </div>
    </div>
  );
}

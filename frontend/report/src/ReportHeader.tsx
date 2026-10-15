import { AppHeader, Button, ButtonLink, ThemeToggle } from '@kindynos/ui';
import { Braces, Download } from 'lucide-react';
import type { ReportData } from './data';
import { servedBy } from './format';
import { useReportI18n } from './messages';
import { openData } from './openData';

/**
 * The logo, and the actions on the report: its archive, when the Kindynos server that made it
 * serves it (a report opened from a file is already saved), its data, and the theme.
 */
export function ReportHeader({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const served = servedBy(data.run_id);
  return (
    <AppHeader
      homeHref={served?.home}
      renderHome={
        served
          ? undefined
          : ({ className, children }) => <span className={className}>{children}</span>
      }
    >
      {served && (
        <ButtonLink href={served.archive} download variant="secondary" icon={<Download />}>
          {t('report.actions.archive')}
        </ButtonLink>
      )}
      <Button variant="secondary" icon={<Braces />} onClick={() => openData(data)}>
        {t('report.actions.data')}
      </Button>
      <ThemeToggle />
    </AppHeader>
  );
}

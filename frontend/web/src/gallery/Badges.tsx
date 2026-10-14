import { Badge, Card, Meter } from '@kindynos/ui';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

export function Badges() {
  const { t } = useWebI18n();
  return (
    <Section id="badges" title={t('gallery.badges.title')} intro={t('gallery.badges.intro')}>
      <div className={styles.row}>
        <Badge tone="high">{t('common.severity.high')}</Badge>
        <Badge tone="medium">{t('common.severity.medium')}</Badge>
        <Badge tone="low">{t('common.severity.low')}</Badge>
        <Badge tone="ai">{t('common.entity.ai')}</Badge>
        <Badge tone="human">{t('common.entity.human')}</Badge>
        <Badge tone="other">{t('common.entity.other')}</Badge>
        <Badge>{t('common.intent.unintentional')}</Badge>
        <Badge>{t('common.timing.post_deployment')}</Badge>
      </div>
      <div className={styles.meters}>
        <Card tone="muted" className={styles.stack}>
          <p className={styles.label}>{t('gallery.badges.score')}</p>
          <p className={styles.score}>
            <span className={styles.scoreValue}>61</span> / 100
          </p>
          {/* The number is right above: the bar only draws it */}
          <Meter value={61} tone="high" />
          <div className={styles.row}>
            <Badge tone="high" on="muted">
              {t('common.severity.high')}
            </Badge>
            <span className={styles.note}>
              {t('gallery.badges.risks', { count: 1 })} · {t('gallery.badges.risks', { count: 34 })}
            </span>
          </div>
        </Card>
        <Card className={styles.stack}>
          <p className={styles.meterHead}>
            <span>{t('gallery.badges.confidence')}</span>
            <strong>94%</strong>
          </p>
          <Meter value={94} size="sm" label={t('gallery.badges.confidence')} valueText="94%" />
        </Card>
      </div>
    </Section>
  );
}

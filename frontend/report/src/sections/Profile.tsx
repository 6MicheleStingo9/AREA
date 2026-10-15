import { Heading } from '@kindynos/ui';
import { angle, point, points, polygon, PROFILE_AXES } from '../charts/radar';
import { useWidth } from '../charts/useWidth';
import type { ProfileAxis, ReportData } from '../data';
import { capitalized, classes, percent } from '../format';
import { useReportI18n, type ReportKey } from '../messages';
import section from './Section.module.css';
import styles from './Profile.module.css';

const SIDES = ['criticality', 'safety'] as const;
type Side = (typeof SIDES)[number];
const LABEL = 14;

/**
 * The alert and safety profile (option C of the redesign): five axes in a web, the criticality
 * indices in one polygon and the safety ones in another. The list beside it gives every index with
 * its value and how it is computed: screen readers read the list.
 */
export function Profile({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const name = (axis: string, side: Side) =>
    t(`report.profile.indices.${axis}.${side}` as ReportKey);
  const [ref, measured] = useWidth<HTMLDivElement>(520);

  // Drawn at the width of its column, up to 560 px: the labels keep the size of the text
  const width = Math.min(560, Math.max(280, Math.floor(measured)));
  const radius = Math.min(170, Math.max(70, (width - 150) / 2));
  const cx = width / 2;
  const cy = radius + 44;
  const height = cy + radius * Math.cos(Math.PI / 5) + 48;
  const shapes = SIDES.map((side) => ({
    side,
    vertices: polygon(data.profile, side, cx, cy, radius),
  }));

  return (
    <section aria-labelledby="profile" className={classes(section.section, section.card)}>
      <div className={section.head}>
        <div className={section.titles}>
          <Heading level={2} id="profile">
            {t('report.profile.title')}
          </Heading>
          <p className={section.lead}>{t('report.profile.lead')}</p>
        </div>
        <ul aria-hidden="true" className={section.legend}>
          {SIDES.map((side) => (
            <li key={side}>
              <span className={classes(section.swatch, section[side])} />
              {t(`report.profile.${side}`)}
            </li>
          ))}
        </ul>
      </div>
      <div className={styles.layout}>
        <div ref={ref} className={styles.chart}>
          <svg
            aria-hidden="true"
            width={width}
            height={height}
            viewBox={`0 0 ${width} ${height}`}
            className={styles.web}
          >
            <g className={styles.grid}>
              {[25, 50, 75, 100].map((ring) => (
                <polygon
                  key={ring}
                  points={points(PROFILE_AXES.map((_, i) => point(i, ring, cx, cy, radius)))}
                />
              ))}
              {PROFILE_AXES.map((axis, i) => {
                const [x, y] = point(i, 100, cx, cy, radius);
                return <line key={axis} x1={cx} y1={cy} x2={x} y2={y} />;
              })}
            </g>
            {shapes.map(({ side, vertices }) => (
              <g key={side} className={styles[side]}>
                <polygon points={points(vertices)} className={styles.shape} />
                {vertices.map(([x, y], i) => (
                  <circle key={i} cx={x} cy={y} r={4.5} className={styles.vertex} />
                ))}
              </g>
            ))}
            <g className={styles.labels}>
              {PROFILE_AXES.map((axis, i) => {
                const text = t(`report.profile.axes.${axis}`);
                const a = angle(i);
                const half = (text.length * LABEL * 0.6) / 2;
                const x = Math.min(width - half, Math.max(half, cx + (radius + 16) * Math.cos(a)));
                const y = cy + (radius + 16) * Math.sin(a) + (Math.sin(a) > 0.5 ? 16 : -6);
                return (
                  <text key={axis} x={x} y={y} textAnchor="middle">
                    {text}
                  </text>
                );
              })}
            </g>
          </svg>
        </div>
        <dl className={styles.indices}>
          {data.profile.map((entry: ProfileAxis) => (
            <div key={entry.axis} className={styles.axis}>
              <dt className={styles.axisName}>{t(`report.profile.axes.${entry.axis}`)}</dt>
              {SIDES.filter((side) => entry[side] !== null).map((side) => (
                <dd key={side} className={styles.index}>
                  <span
                    aria-hidden="true"
                    className={classes(section.swatch, section.dot, section[side])}
                  />
                  <span>
                    <span className={styles.indexName}>
                      {capitalized(name(entry.axis, side))}{' '}
                      <strong className={styles.value}>{percent(entry[side])}</strong>
                    </span>{' '}
                    <span className={styles.definition}>
                      {t(`report.profile.definitions.${entry.axis}.${side}` as ReportKey)}
                    </span>
                  </span>
                </dd>
              ))}
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

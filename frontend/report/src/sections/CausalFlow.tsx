import { Heading } from '@kindynos/ui';
import { useMemo, useState, type PointerEvent } from 'react';
import { bandPath, layoutFlow, type FlowBand, type FlowNode } from '../charts/flow';
import { useWidth } from '../charts/useWidth';
import { AXES, type Axis, type ReportData } from '../data';
import { causeKey, classes } from '../format';
import { useReportI18n, type ReportKey } from '../messages';
import section from './Section.module.css';
import styles from './CausalFlow.module.css';

// The diagram in CSS pixels: drawn at the width of its card, so that its text keeps its size
const HEIGHT = 360;
const GAP = 18;
const NODE = 14;
// The space between a node and its label, and around a label
const PAD = 10;
// Never narrower than this: on a phone the diagram scrolls in its card
const MIN_WIDTH = 560;

/** The width of a label, near enough: Inter semibold at 15 px */
const textWidth = (text: string) => Math.ceil(text.length * 8.6);

interface Hover {
  band: FlowBand;
  x: number;
  y: number;
}

/**
 * The causes of the risks as a Sankey diagram: from the entity to the intent to the timing, each
 * band as thick as its risks. Screen readers read the same flows from a table.
 */
export function CausalFlow({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const [ref, measured] = useWidth<HTMLDivElement>(960);
  const layout = useMemo(() => layoutFlow(data.flow, HEIGHT, GAP), [data.flow]);
  const [hover, setHover] = useState<Hover | null>(null);

  const label = (node: { axis: Axis; value: string }) =>
    t(causeKey(node.axis, node.value) as ReportKey);
  const nodeText = (node: FlowNode) =>
    t('report.flow.node', { label: label(node), count: node.count });
  const risks = (count: number) => t('report.flow.risks', { count });

  // Each column's labels right of its nodes, in a space of their own: none can cover another
  const widest = (axis: Axis) =>
    Math.max(0, ...layout.columns[axis].map((n) => textWidth(nodeText(n))));
  const last = widest('timing') + 2 * PAD;
  const zone = Math.max(widest('entity'), widest('intent')) + 2 * PAD;
  const fits = Math.max(MIN_WIDTH, 2 * (zone + NODE) + NODE + last);
  const width = Math.max(fits, Math.floor(measured));
  const scrolls = measured < fits;
  const timing = width - last - NODE;
  const left: Record<Axis, number> = { entity: 0, intent: timing / 2, timing };

  const track = (band: FlowBand) => (event: PointerEvent<SVGPathElement>) => {
    const box = event.currentTarget.ownerSVGElement?.getBoundingClientRect();
    setHover({ band, x: event.clientX - (box?.left ?? 0), y: event.clientY - (box?.top ?? 0) });
  };

  return (
    <section aria-labelledby="flow" className={classes(section.section, section.card)}>
      <div className={section.titles}>
        <Heading level={2} id="flow">
          {t('report.flow.title')}
        </Heading>
        <p className={section.lead}>{t('report.flow.lead')}</p>
      </div>
      <div
        ref={ref}
        className={section.scroll}
        // Scrolling, the diagram takes the focus, for the arrow keys
        tabIndex={scrolls ? 0 : undefined}
        role={scrolls ? 'group' : undefined}
        aria-label={scrolls ? t('report.flow.title') : undefined}
      >
        <div className={styles.figure} style={{ width }}>
          <div aria-hidden="true" className={styles.axes}>
            {AXES.map((axis) => (
              <span key={axis} style={{ left: left[axis] }}>
                {t(`report.axes.${axis}`)}
              </span>
            ))}
          </div>
          <svg
            aria-hidden="true"
            className={styles.diagram}
            width={width}
            height={HEIGHT}
            viewBox={`0 0 ${width} ${HEIGHT}`}
            onPointerLeave={() => setHover(null)}
          >
            {layout.bands.map((band, i) => (
              <path
                key={i}
                d={bandPath(band, left[band.from.axis] + NODE, left[band.to.axis])}
                className={classes(
                  styles.band,
                  band.from.axis === 'entity' ? styles[band.from.value] : styles.later,
                  hover?.band === band && styles.active,
                )}
                onPointerEnter={track(band)}
                onPointerMove={track(band)}
              />
            ))}
            {AXES.map((axis) =>
              layout.columns[axis].map((node) => (
                <rect
                  key={`${axis}-${node.value}`}
                  x={left[axis]}
                  y={node.y}
                  width={NODE}
                  height={Math.max(node.height, 2)}
                  rx={3}
                  className={classes(
                    styles.node,
                    axis === 'entity' ? styles[node.value] : styles[axis],
                  )}
                />
              )),
            )}
            <g className={styles.labels}>
              {AXES.map((axis) =>
                layout.columns[axis].map((node: FlowNode) => (
                  <text
                    key={`${axis}-${node.value}`}
                    x={left[axis] + NODE + PAD}
                    y={node.y + node.height / 2}
                    dominantBaseline="middle"
                  >
                    {nodeText(node)}
                  </text>
                )),
              )}
            </g>
          </svg>
          {hover && (
            <div
              aria-hidden="true"
              className={styles.tooltip}
              style={{ left: hover.x, top: hover.y + 32 }}
            >
              <strong>
                {t('report.flow.band', { from: label(hover.band.from), to: label(hover.band.to) })}
              </strong>
              <span>{risks(hover.band.count)}</span>
            </div>
          )}
        </div>
      </div>
      {scrolls && <p className={section.note}>{t('report.flow.scroll')}</p>}
      {layout.missing.length > 0 && (
        <p className={section.note}>
          {t('report.flow.none', {
            labels: layout.missing
              .map((node) =>
                t('report.flow.value', {
                  value: label(node),
                  axis: t(`report.axes.${node.axis}`).toLowerCase(),
                }),
              )
              .join(', '),
          })}
        </p>
      )}
      {/* A table keeps the width of its text: the frame out of sight is around it */}
      <div className={section.hidden}>
        <table>
          <caption>{t('report.flow.label')}</caption>
          <thead>
            <tr>
              <th scope="col">{t('report.flow.from')}</th>
              <th scope="col">{t('report.flow.to')}</th>
              <th scope="col">{t('report.flow.count')}</th>
            </tr>
          </thead>
          <tbody>
            {layout.bands.map((band, i) => (
              <tr key={i}>
                <td>
                  {t(`report.axes.${band.from.axis}`)}: {label(band.from)}
                </td>
                <td>
                  {t(`report.axes.${band.to.axis}`)}: {label(band.to)}
                </td>
                <td>{band.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

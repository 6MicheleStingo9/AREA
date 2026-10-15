import { AXES, CAUSES, type Axis, type FlowLink, type ReportData } from '../data';

/** A value of a causal axis in the diagram: a column of nodes per axis */
export interface FlowNode {
  axis: Axis;
  value: string;
  count: number;
  /** Its top and its height, in the units of the diagram */
  y: number;
  height: number;
}

/** The risks that go from a value of an axis to a value of the next one */
export interface FlowBand {
  from: FlowNode;
  to: FlowNode;
  count: number;
  /** Where the band leaves its source and reaches its target (its top), and how thick it is */
  y0: number;
  y1: number;
  thickness: number;
}

export interface FlowLayout {
  /** The nodes of each axis, top to bottom */
  columns: Record<Axis, FlowNode[]>;
  bands: FlowBand[];
  /** The values that no risk has */
  missing: { axis: Axis; value: string }[];
}

type Flow = ReportData['flow'];

/** How many risks have each value of an axis */
function totals(axis: Axis, flow: Flow): Map<string, number> {
  const count = new Map<string, number>();
  const add = (value: string, n: number) => count.set(value, (count.get(value) ?? 0) + n);
  if (axis === 'entity') flow.entity_intent.forEach((link) => add(link.from, link.count));
  if (axis === 'intent') flow.entity_intent.forEach((link) => add(link.to, link.count));
  if (axis === 'timing') flow.intent_timing.forEach((link) => add(link.to, link.count));
  return count;
}

/**
 * The order of the nodes of an axis: by the mean position of the nodes they come from, so that fewer
 * bands cross, with "other" last.
 */
function order(values: string[], incoming: FlowLink[], previous: FlowNode[]): string[] {
  const position = new Map(previous.map((node, i) => [node.value, i]));
  const centre = (value: string) => {
    let sum = 0;
    let n = 0;
    for (const link of incoming) {
      if (link.to !== value) continue;
      sum += (position.get(link.from) ?? 0) * link.count;
      n += link.count;
    }
    return n ? sum / n : Infinity;
  };
  return [...values].sort((a, b) => {
    if ((a === 'other') !== (b === 'other')) return a === 'other' ? 1 : -1;
    return centre(a) - centre(b) || values.indexOf(a) - values.indexOf(b);
  });
}

/** Where each band leaves its source and reaches its target: in the order of the nodes at the other end */
function place(
  links: FlowLink[],
  sources: FlowNode[],
  targets: FlowNode[],
  unit: number,
): FlowBand[] {
  const bands: FlowBand[] = [];
  for (const link of links) {
    const from = sources.find((node) => node.value === link.from);
    const to = targets.find((node) => node.value === link.to);
    if (from && to && link.count > 0) {
      bands.push({ from, to, count: link.count, y0: 0, y1: 0, thickness: link.count * unit });
    }
  }
  const rank = (nodes: FlowNode[], node: FlowNode) => nodes.indexOf(node);
  const stackAt = (end: 'from' | 'to', other: 'from' | 'to', key: 'y0' | 'y1') => {
    const offset = new Map<FlowNode, number>();
    const ordered = [...bands].sort(
      (a, b) =>
        rank(end === 'from' ? sources : targets, a[end]) -
          rank(end === 'from' ? sources : targets, b[end]) ||
        rank(other === 'from' ? sources : targets, a[other]) -
          rank(other === 'from' ? sources : targets, b[other]),
    );
    for (const band of ordered) {
      const below = offset.get(band[end]) ?? 0;
      band[key] = band[end].y + below;
      offset.set(band[end], below + band.thickness);
    }
  };
  stackAt('from', 'to', 'y0');
  stackAt('to', 'from', 'y1');
  return bands;
}

/**
 * The flow of the risks from their entity to their intent to their timing, as a Sankey diagram of
 * the given height: each node as tall as its risks, gap units from the next; every axis at the same
 * scale, so that a band is as thick at both ends.
 */
export function layoutFlow(flow: Flow, height: number, gap: number): FlowLayout {
  const found = {
    entity: totals('entity', flow),
    intent: totals('intent', flow),
    timing: totals('timing', flow),
  };
  const values = (axis: Axis): readonly string[] => CAUSES[axis];
  const present = (axis: Axis) => values(axis).filter((value) => found[axis].get(value));
  const missing = AXES.flatMap((axis) =>
    values(axis)
      .filter((value) => !found[axis].get(value))
      .map((value) => ({ axis, value })),
  );

  const most = Math.max(1, ...AXES.map((axis) => present(axis).length));
  const risks = Math.max(
    1,
    ...AXES.map((axis) => [...found[axis].values()].reduce((sum, n) => sum + n, 0)),
  );
  const unit = (height - gap * (most - 1)) / risks;

  const stack = (axis: Axis, ordered: string[]): FlowNode[] => {
    let y = 0;
    return ordered.map((value) => {
      const count = found[axis].get(value) ?? 0;
      const node = { axis, value, count, y, height: count * unit };
      y += node.height + gap;
      return node;
    });
  };
  const entity = stack('entity', present('entity'));
  const intent = stack('intent', order(present('intent'), flow.entity_intent, entity));
  const timing = stack('timing', order(present('timing'), flow.intent_timing, intent));

  return {
    columns: { entity, intent, timing },
    bands: [
      ...place(flow.entity_intent, entity, intent, unit),
      ...place(flow.intent_timing, intent, timing, unit),
    ],
    missing,
  };
}

/** The outline of a band, from the right edge of its source (x0) to the left edge of its target (x1) */
export function bandPath(band: FlowBand, x0: number, x1: number): string {
  const middle = (x0 + x1) / 2;
  const { y0, y1, thickness: t } = band;
  return [
    `M${x0},${y0}`,
    `C${middle},${y0} ${middle},${y1} ${x1},${y1}`,
    `L${x1},${y1 + t}`,
    `C${middle},${y1 + t} ${middle},${y0 + t} ${x0},${y0 + t}`,
    'Z',
  ].join(' ');
}

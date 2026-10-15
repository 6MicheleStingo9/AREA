import { describe, expect, it } from 'vitest';
import { EXAMPLE } from '../test/report';
import { bandPath, layoutFlow } from './flow';
import { heat } from './heat';
import { point, polygon } from './radar';

describe('the causal flow', () => {
  const layout = layoutFlow(EXAMPLE.flow, 360, 18);

  it('has a node for every value that some risk has, as tall as its risks', () => {
    const column = (axis: 'entity' | 'intent' | 'timing') =>
      layout.columns[axis].map((node) => [node.value, node.count]);
    expect(column('entity')).toEqual([
      ['ai', 19],
      ['human', 14],
      ['other', 1],
    ]);
    // Unintentional first: the AI risks, at the top, mostly go there; "other" always last
    expect(column('intent')).toEqual([
      ['unintentional', 23],
      ['intentional', 11],
    ]);
    expect(column('timing')).toEqual([
      ['post-deployment', 31],
      ['other', 3],
    ]);
    expect(layout.missing).toEqual([
      { axis: 'intent', value: 'other' },
      { axis: 'timing', value: 'pre-deployment' },
    ]);
  });

  it('draws every axis at the same scale, in the height of the diagram', () => {
    const entity = layout.columns.entity;
    const last = entity[entity.length - 1];
    expect(last && last.y + last.height).toBeCloseTo(360);
    const unit = (entity[0]?.height ?? 0) / 19;
    for (const axis of ['intent', 'timing'] as const) {
      for (const node of layout.columns[axis]) expect(node.height).toBeCloseTo(node.count * unit);
    }
  });

  it('stacks the bands of a node without a gap, in the order of the nodes at their other end', () => {
    const ai = layout.columns.entity[0];
    const fromAi = layout.bands.filter((band) => band.from === ai).sort((a, b) => a.y0 - b.y0);
    // AI to unintentional (the upper intent node) leaves from the top of the AI node
    expect(fromAi.map((band) => band.to.value)).toEqual(['unintentional', 'intentional']);
    expect(fromAi[0]?.y0).toBeCloseTo(ai?.y ?? -1);
    expect(fromAi[1]?.y0).toBeCloseTo((ai?.y ?? 0) + (fromAi[0]?.thickness ?? 0));
    const unintentional = layout.columns.intent[0];
    const into = layout.bands
      .filter((band) => band.to === unintentional)
      .sort((a, b) => a.y1 - b.y1);
    expect(into.reduce((sum, band) => sum + band.thickness, 0)).toBeCloseTo(
      unintentional?.height ?? 0,
    );
    expect(into.map((band) => band.from.value)).toEqual(['ai', 'human', 'other']);
  });

  it('outlines a band from the edge of its source to the edge of its target', () => {
    const band = layout.bands[0];
    if (!band) throw new Error('no band');
    const path = bandPath(band, 14, 500);
    expect(path.startsWith(`M14,${band.y0}`)).toBe(true);
    expect(path).toContain(`500,${band.y1}`);
    expect(path.endsWith('Z')).toBe(true);
  });
});

describe('the profile', () => {
  it('puts 100 at the end of an axis, the first one pointing up', () => {
    const [x, y] = point(0, 100, 200, 200, 100);
    expect(x).toBeCloseTo(200);
    expect(y).toBeCloseTo(100);
  });

  it('skips the axes that have no index of a profile, not drawing them at the centre', () => {
    // Exposure has no safety index, entity no criticality one
    expect(polygon(EXAMPLE.profile, 'criticality', 0, 0, 100)).toHaveLength(4);
    const safety = polygon(EXAMPLE.profile, 'safety', 0, 0, 100);
    expect(safety).toHaveLength(4);
    // Preventability is 0: that vertex is at the centre, because the value is zero
    expect(safety[1]?.[0]).toBeCloseTo(0);
    expect(safety[1]?.[1]).toBeCloseTo(0);
  });
});

describe('the patterns', () => {
  it('darken in four steps, up to the pattern with the most risks', () => {
    expect([0, 1, 4, 5, 9, 10, 14, 18].map((count) => heat(count, 18))).toEqual([
      0, 1, 1, 2, 2, 3, 4, 4,
    ]);
    expect(heat(0, 0)).toBe(0);
  });
});

import type { ProfileAxis, ProfileAxisName } from '../data';

/** The five axes of the profile, clockwise from the top */
export const PROFILE_AXES: readonly ProfileAxisName[] = [
  'severity',
  'exposure',
  'prevention',
  'intent',
  'entity',
];

export type Point = [x: number, y: number];

/** The angle of an axis, in radians: the first one points up */
export function angle(index: number): number {
  return ((-90 + (360 / PROFILE_AXES.length) * index) * Math.PI) / 180;
}

/** Where a value (0-100) sits on an axis of a web centred at (cx, cy), of the given radius */
export function point(index: number, value: number, cx: number, cy: number, radius: number): Point {
  const r = (radius * Math.min(100, Math.max(0, value))) / 100;
  return [cx + r * Math.cos(angle(index)), cy + r * Math.sin(angle(index))];
}

/**
 * The polygon of a profile (criticality or safety): one vertex per axis that has an index of that
 * profile. An axis without one (exposure has no safety index, entity no criticality one) is skipped,
 * not drawn at the centre, which would read as zero.
 */
export function polygon(
  profile: ProfileAxis[],
  side: 'criticality' | 'safety',
  cx: number,
  cy: number,
  radius: number,
): Point[] {
  return PROFILE_AXES.flatMap((axis, i) => {
    const value = profile.find((entry) => entry.axis === axis)?.[side];
    return value === null || value === undefined ? [] : [point(i, value, cx, cy, radius)];
  });
}

/** Points as an SVG attribute */
export function points(list: Point[]): string {
  return list.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
}

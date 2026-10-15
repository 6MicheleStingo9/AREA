/**
 * How dark a pattern is, from its risks: four steps up to the pattern with the most. Steps, not a
 * gradient, so that its text keeps its contrast in both themes (Patterns.module.css).
 */
export function heat(count: number, most: number): 0 | 1 | 2 | 3 | 4 {
  if (count <= 0 || most <= 0) return 0;
  return Math.min(4, Math.ceil((count / most) * 4)) as 1 | 2 | 3 | 4;
}

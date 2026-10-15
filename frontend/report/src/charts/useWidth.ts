import { useEffect, useRef, useState } from 'react';

/**
 * The width of an element in CSS pixels, followed as the page resizes: a chart drawn at that width
 * keeps its text at the size of the page's. The fallback holds until the first measure.
 */
export function useWidth<T extends HTMLElement>(fallback: number) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const element = ref.current;
    if (!element || typeof ResizeObserver === 'undefined') return;
    // The observer measures once as it starts, then on every change
    const observer = new ResizeObserver(([entry]) => {
      if (entry && entry.contentRect.width > 0) setWidth(entry.contentRect.width);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

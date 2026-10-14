import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import { installMatchMedia } from './ui/src/test/system-theme';

beforeEach(() => {
  installMatchMedia();
  // jsdom does not scroll: the router restores the scroll on every page
  window.scrollTo = () => {};
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
  document.documentElement.removeAttribute('lang');
});

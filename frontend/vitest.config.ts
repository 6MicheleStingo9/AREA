import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    projects: [
      {
        extends: true,
        test: {
          name: 'dom',
          environment: 'jsdom',
          include: ['{ui,web}/src/**/*.test.{ts,tsx}'],
          exclude: ['**/*.node.test.ts'],
          setupFiles: ['./vitest.setup.ts'],
        },
      },
      {
        // The tests that read files from the disk
        extends: true,
        test: { name: 'node', environment: 'node', include: ['{ui,web}/src/**/*.node.test.ts'] },
      },
    ],
  },
});

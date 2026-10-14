import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, searchForWorkspaceRoot } from 'vite';

// The strings (locales/) and the logo (files/img/brand/) are in the repository, outside frontend/
const repository = fileURLToPath(new URL('../..', import.meta.url));

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: [
        searchForWorkspaceRoot(process.cwd()),
        `${repository}locales`,
        `${repository}files/img/brand`,
      ],
    },
  },
});

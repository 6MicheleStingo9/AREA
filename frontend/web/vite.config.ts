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
    // The API and the reports come from FastAPI (uvicorn api.main:app, on port 8000)
    proxy: { '/api': 'http://127.0.0.1:8000', '/report': 'http://127.0.0.1:8000' },
  },
});

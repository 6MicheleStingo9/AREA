import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, searchForWorkspaceRoot, type Plugin } from 'vite';

// The strings (locales/) and the logo (files/img/brand/) are in the repository, outside frontend/
const repository = fileURLToPath(new URL('../..', import.meta.url));

/**
 * The report is a single HTML file, which opens offline and from any folder: its script and its
 * styles go into the page, and the files they use (fonts, logo) into them, as data: URLs.
 */
function singleFile(): Plugin {
  return {
    name: 'kindynos:single-file',
    enforce: 'post',
    generateBundle(_, bundle) {
      const page = bundle['index.html'];
      if (page?.type !== 'asset' || typeof page.source !== 'string') {
        return this.error('the build has no index.html');
      }
      let html = page.source;
      for (const [name, file] of Object.entries(bundle)) {
        if (name === 'index.html') continue;
        const path = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (file.type === 'chunk') {
          const tag = new RegExp(`<script type="module" crossorigin src="[^"]*${path}"></script>`);
          if (!tag.test(html)) return this.error(`${name} is not the script of the page`);
          // A "</script" in the code would end the element: in a string it reads the same escaped
          const code = file.code.replaceAll('</script', '<\\/script');
          html = html.replace(tag, () => `<script type="module">${code}</script>`);
        } else if (name.endsWith('.css') && typeof file.source === 'string') {
          const tag = new RegExp(`<link rel="stylesheet" crossorigin href="[^"]*${path}">`);
          if (!tag.test(html) || file.source.includes('</style')) {
            return this.error(`${name} cannot go into the page`);
          }
          const css = file.source;
          html = html.replace(tag, () => `<style>${css}</style>`);
        } else {
          return this.error(`${name} would stay out of the page`);
        }
        delete bundle[name];
      }
      page.source = html;
    },
  };
}

export default defineConfig({
  plugins: [react(), singleFile()],
  base: './',
  build: {
    assetsInlineLimit: () => true,
    cssCodeSplit: false,
    modulePreload: false,
    rolldownOptions: { output: { codeSplitting: false } },
  },
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

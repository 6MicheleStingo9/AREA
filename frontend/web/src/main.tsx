import '@kindynos/ui/styles.css';
import { I18nProvider, ThemeProvider } from '@kindynos/ui';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { messages } from './messages';

const root = document.getElementById('root');
if (!root) throw new Error('index.html has no #root');

createRoot(root).render(
  <StrictMode>
    <ThemeProvider>
      <I18nProvider messages={messages}>
        <App />
      </I18nProvider>
    </ThemeProvider>
  </StrictMode>,
);

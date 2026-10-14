import '@kindynos/ui/styles.css';
import { I18nProvider, ThemeProvider } from '@kindynos/ui';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router';
import { messages } from './messages';
import { AssessmentProvider } from './questionnaire/AssessmentProvider';
import { router } from './router';

const root = document.getElementById('root');
if (!root) throw new Error('index.html has no #root');

createRoot(root).render(
  <StrictMode>
    <ThemeProvider>
      <I18nProvider messages={messages}>
        <AssessmentProvider>
          <RouterProvider router={router} />
        </AssessmentProvider>
      </I18nProvider>
    </ThemeProvider>
  </StrictMode>,
);

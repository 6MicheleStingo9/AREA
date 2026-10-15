import { createBrowserRouter, type RouteObject } from 'react-router';
import { Layout } from './Layout';
import { Analysis } from './pages/Analysis';
import { NotFound } from './pages/NotFound';
import { PageError } from './pages/PageError';
import { QuestionPage } from './pages/QuestionPage';
import { Review } from './pages/Review';
import { Welcome } from './pages/Welcome';

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      {
        // A page that fails (the questionnaire did not load) shows its error inside the layout
        errorElement: <PageError />,
        children: [
          { index: true, element: <Welcome /> },
          { path: 'questions/:id', element: <QuestionPage /> },
          { path: 'review', element: <Review /> },
          { path: 'analysis/:runId', element: <Analysis /> },
          {
            // The components of the interface, for its development: loaded only here
            path: 'ui',
            lazy: async () => ({ Component: (await import('./gallery/GalleryPage')).GalleryPage }),
          },
          { path: '*', element: <NotFound /> },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);

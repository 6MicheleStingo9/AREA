import { useEffect } from 'react';

/** The title of the page, in the tab and in the history */
export function useDocumentTitle(title: string): void {
  useEffect(() => {
    document.title = title;
  }, [title]);
}

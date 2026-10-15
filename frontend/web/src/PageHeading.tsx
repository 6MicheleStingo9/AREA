import { Heading } from '@kindynos/ui';
import { useEffect, useRef, type ComponentProps } from 'react';
import { NavigationType, useLocation, useNavigationType } from 'react-router';

/**
 * The title of a page. After a link or a button changed the page, it takes the focus, so that a
 * screen reader reads the new page from its title, and the next Tab starts from there.
 */
export function PageHeading(
  props: Omit<ComponentProps<typeof Heading>, 'level' | 'ref' | 'tabIndex'>,
) {
  const ref = useRef<HTMLHeadingElement>(null);
  const { pathname } = useLocation();
  // The first page of a visit, and back and forward, leave the focus to the browser
  const navigated = useNavigationType() !== NavigationType.Pop;
  useEffect(() => {
    if (navigated) ref.current?.focus();
  }, [pathname, navigated]);
  return <Heading level={1} ref={ref} tabIndex={-1} {...props} />;
}

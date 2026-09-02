import type {AuthSessionSurface} from '@/lib/auth-session-events';

export function buildLoginRedirectHref({
  locale,
  pathname,
  search = '',
  surface = 'candidate',
}: {
  locale: string;
  pathname: string;
  search?: string;
  surface?: AuthSessionSurface;
}): string {
  const currentPath = `${pathname}${search}`;
  const params = new URLSearchParams();

  if (surface === 'employer') {
    params.set('role', 'employer');
  }

  if (pathname && !pathname.endsWith('/login')) {
    params.set('redirect', currentPath);
  }

  const query = params.toString();
  return `/${locale}/login${query ? `?${query}` : ''}`;
}

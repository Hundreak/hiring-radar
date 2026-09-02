export type AuthSessionSurface = 'candidate' | 'employer' | 'unknown';

export interface AuthSessionExpiredDetail {
  surface: AuthSessionSurface;
  path: string;
  detail: string;
  requestId: string | null;
  status: number;
}

export const AUTH_SESSION_EXPIRED_EVENT = 'noytera:auth-session-expired';

const USER_AUTH_START_ENDPOINTS = new Set([
  '/user/auth/login-password',
  '/user/auth/request-magic-link',
  '/user/auth/consume-magic-link',
  '/user/auth/request-password-reset',
  '/user/auth/confirm-password-reset',
]);

const EMPLOYER_AUTH_START_ENDPOINTS = new Set([
  '/employer/auth/login',
  '/employer/auth/register',
]);

function normalizeApiPath(path: string): string {
  const [pathname] = path.split('?');
  const normalized = pathname || path;
  return normalized.startsWith('/api/') ? normalized.slice(4) : normalized;
}

export function getSessionSurfaceForPath(path: string): AuthSessionSurface {
  const pathname = normalizeApiPath(path);
  if (pathname.startsWith('/employer/')) {
    return 'employer';
  }
  if (pathname.startsWith('/user/')) {
    return 'candidate';
  }
  return 'unknown';
}

export function shouldEmitSessionExpired(path: string, status: number): boolean {
  if (status !== 401) {
    return false;
  }

  const pathname = normalizeApiPath(path);

  if (pathname.startsWith('/public/')) {
    return false;
  }

  if (USER_AUTH_START_ENDPOINTS.has(pathname) || EMPLOYER_AUTH_START_ENDPOINTS.has(pathname)) {
    return false;
  }

  return pathname.startsWith('/user/') || pathname.startsWith('/employer/');
}

export function emitSessionExpired(detail: AuthSessionExpiredDetail): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent<AuthSessionExpiredDetail>(AUTH_SESSION_EXPIRED_EVENT, {detail}));
}

export function emitSessionExpiredFromApiError(path: string, error: {status: number; detail: string; requestId: string | null}): void {
  if (!shouldEmitSessionExpired(path, error.status)) {
    return;
  }

  emitSessionExpired({
    surface: getSessionSurfaceForPath(path),
    path,
    detail: error.detail,
    requestId: error.requestId,
    status: error.status,
  });
}

export function onSessionExpired(
  listener: (detail: AuthSessionExpiredDetail) => void
): () => void {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  const handler = (event: Event) => {
    listener((event as CustomEvent<AuthSessionExpiredDetail>).detail);
  };

  window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handler);
  return () => window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handler);
}

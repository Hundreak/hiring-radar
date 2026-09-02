import {ApiError} from '@/lib/api';

export type ApiErrorKind =
  | 'offline'
  | 'network'
  | 'unauthorized'
  | 'forbidden'
  | 'notFound'
  | 'conflict'
  | 'validation'
  | 'rateLimited'
  | 'server'
  | 'unknown';

export type ErrorRecoveryInfo = {
  kind: ApiErrorKind;
  status: number | null;
  detail: string;
  retryable: boolean;
  retryAfterSeconds: number | null;
  requestId: string | null;
};

// Yalnizca gecici arizalar yeniden denenir. 4xx ailesindeki hatalar ayni
// istekle duzelmez; kullaniciya once ne yapmasi gerektigi soylenmelidir.
const RETRYABLE_KINDS: ReadonlySet<ApiErrorKind> = new Set<ApiErrorKind>([
  'offline',
  'network',
  'rateLimited',
  'server',
]);

function kindFromStatus(status: number): ApiErrorKind {
  if (status === 401) return 'unauthorized';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'notFound';
  if (status === 409) return 'conflict';
  if (status === 422) return 'validation';
  if (status === 429) return 'rateLimited';
  if (status >= 500) return 'server';
  return 'unknown';
}

function isOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

function isTransportFailure(error: Error): boolean {
  // fetch() aga ulasamadiginda TypeError firlatir; mesaj metni tarayiciya gore
  // degistigi icin tip kontrolu birincil, metin esleme yedek sinyaldir.
  return error instanceof TypeError || /fetch|network|connection/i.test(error.message);
}

export function classifyApiError(error: unknown): ErrorRecoveryInfo {
  if (error instanceof ApiError) {
    const kind = kindFromStatus(error.status);

    return {
      kind,
      status: error.status,
      detail: error.detail || error.message || 'Request failed.',
      retryable: RETRYABLE_KINDS.has(kind),
      retryAfterSeconds: error.retryAfterSeconds,
      requestId: error.requestId,
    };
  }

  if (error instanceof Error) {
    if (isOffline()) {
      return {
        kind: 'offline',
        status: null,
        detail: error.message || 'The device appears to be offline.',
        retryable: true,
        retryAfterSeconds: null,
        requestId: null,
      };
    }

    const transport = isTransportFailure(error);

    return {
      kind: transport ? 'network' : 'unknown',
      status: null,
      detail: error.message || 'Request failed.',
      retryable: transport,
      retryAfterSeconds: null,
      requestId: null,
    };
  }

  return {
    kind: 'unknown',
    status: null,
    detail: typeof error === 'string' && error ? error : 'Request failed.',
    retryable: false,
    retryAfterSeconds: null,
    requestId: null,
  };
}

export function shouldRetryApiQuery(error: unknown): boolean {
  return classifyApiError(error).retryable;
}

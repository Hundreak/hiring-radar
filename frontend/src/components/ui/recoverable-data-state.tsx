'use client';

import {CloudOff, Loader2, Lock, RefreshCw, SearchX, ShieldAlert, TriangleAlert} from 'lucide-react';

import {Button} from '@/components/ui/button';
import type {ApiErrorKind, ErrorRecoveryInfo} from '@/lib/api-error-ui';
import {cn} from '@/lib/utils';

type RecoverableDataStateLabels = {
  title: string;
  hint: string;
  retry: string;
  retrying: string;
  requestId: string;
  retryAfter: (seconds: number) => string;
};

const ICONS: Record<ApiErrorKind, typeof TriangleAlert> = {
  offline: CloudOff,
  network: CloudOff,
  unauthorized: Lock,
  forbidden: ShieldAlert,
  notFound: SearchX,
  conflict: TriangleAlert,
  validation: TriangleAlert,
  rateLimited: TriangleAlert,
  server: TriangleAlert,
  unknown: TriangleAlert,
};

const COPY: Record<'tr' | 'en', {kinds: Record<ApiErrorKind, {title: string; hint: string}>; chrome: Omit<RecoverableDataStateLabels, 'title' | 'hint'>}> = {
  tr: {
    kinds: {
      offline: {title: 'Baglanti yok', hint: 'Cihaz cevrimdisi gorunuyor. Baglanti geri geldiginde tekrar dene.'},
      network: {title: 'Sunucuya ulasilamadi', hint: 'Ag istegi tamamlanmadi. Birkac saniye sonra tekrar denemek genelde yeterlidir.'},
      unauthorized: {title: 'Oturum dogrulanamadi', hint: 'Oturumun sona ermis olabilir. Yeniden giris yaptiktan sonra bu ekrani tazele.'},
      forbidden: {title: 'Bu kayitlara erisim yetkin yok', hint: 'Gerekli yetki tanimlandiktan sonra kayitlar burada listelenir.'},
      notFound: {title: 'Kayit bulunamadi', hint: 'Aradigin kayit tasinmis veya silinmis olabilir. Filtreleri sadelestirip tekrar dene.'},
      conflict: {title: 'Kayit bu sirada degisti', hint: 'Baska bir islem ayni kaydi guncelledi. Tazeleyip son halini gor.'},
      validation: {title: 'Filtreler islenemedi', hint: 'Gonderilen filtre degerleri gecersiz. Alanlari sadelestirip tekrar dene.'},
      rateLimited: {title: 'Cok fazla istek gonderildi', hint: 'Istek limiti asildi. Kisa bir bekleyisin ardindan devam edebilirsin.'},
      server: {title: 'Sunucu tarafinda bir hata olustu', hint: 'Hata kaydedildi. Tekrar denemek cogu durumda sonucu getirir.'},
      unknown: {title: 'Veriler yuklenemedi', hint: 'Beklenmeyen bir hata olustu. Tekrar denemek isterseniz asagidaki dugmeyi kullanin.'},
    },
    chrome: {
      retry: 'Tekrar dene',
      retrying: 'Yenileniyor...',
      requestId: 'Istek kimligi',
      retryAfter: (seconds) => `Onerilen bekleme suresi: ${seconds} saniye.`,
    },
  },
  en: {
    kinds: {
      offline: {title: 'No connection', hint: 'This device appears to be offline. Try again once the connection is back.'},
      network: {title: 'Could not reach the server', hint: 'The network request did not complete. Retrying in a few seconds usually resolves it.'},
      unauthorized: {title: 'Session could not be verified', hint: 'Your session may have expired. Sign in again and refresh this view.'},
      forbidden: {title: 'You do not have access to these records', hint: 'Once the required permission is granted, the records will appear here.'},
      notFound: {title: 'Records not found', hint: 'What you are looking for may have moved or been deleted. Simplify the filters and try again.'},
      conflict: {title: 'The record changed meanwhile', hint: 'Another operation updated the same record. Refresh to see its latest state.'},
      validation: {title: 'Filters could not be processed', hint: 'The submitted filter values are invalid. Simplify the fields and try again.'},
      rateLimited: {title: 'Too many requests', hint: 'The request limit was exceeded. You can continue after a short wait.'},
      server: {title: 'Something failed on the server', hint: 'The error has been recorded. Retrying resolves it in most cases.'},
      unknown: {title: 'Data could not be loaded', hint: 'An unexpected error occurred. Use the button below to try again.'},
    },
    chrome: {
      retry: 'Try again',
      retrying: 'Refreshing...',
      requestId: 'Request ID',
      retryAfter: (seconds) => `Suggested wait: ${seconds} seconds.`,
    },
  },
};

function language(locale: string): 'tr' | 'en' {
  return locale.toLowerCase().startsWith('tr') ? 'tr' : 'en';
}

export function RecoverableDataState({
  error,
  onRetry,
  retrying = false,
  locale = 'tr',
  labels,
  className,
}: {
  error: ErrorRecoveryInfo;
  onRetry: () => void;
  retrying?: boolean;
  locale?: string;
  labels?: Partial<RecoverableDataStateLabels>;
  className?: string;
}) {
  const copy = COPY[language(locale)];
  const kindCopy = copy.kinds[error.kind];
  const title = labels?.title ?? kindCopy.title;
  const hint = labels?.hint ?? kindCopy.hint;
  const retryLabel = labels?.retry ?? copy.chrome.retry;
  const retryingLabel = labels?.retrying ?? copy.chrome.retrying;
  const requestIdLabel = labels?.requestId ?? copy.chrome.requestId;
  const retryAfterLabel = labels?.retryAfter ?? copy.chrome.retryAfter;
  const Icon = ICONS[error.kind];

  return (
    <div
      role="alert"
      aria-busy={retrying}
      className={cn(
        'rounded-[28px] border border-danger/25 bg-danger/[0.06] p-6 sm:p-8',
        className
      )}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-2xl border border-danger/20 bg-danger/10 text-danger">
          <Icon className="size-5" />
        </span>

        <div className="min-w-0 flex-1 space-y-2">
          <h3 className="text-base font-black tracking-[-0.02em] text-foreground">{title}</h3>
          <p className="text-sm leading-6 text-muted-foreground">{hint}</p>

          {error.detail && error.detail !== hint ? (
            <p className="text-sm font-medium leading-6 text-foreground/80">{error.detail}</p>
          ) : null}

          {error.retryAfterSeconds ? (
            <p className="text-xs font-bold text-muted-foreground">{retryAfterLabel(error.retryAfterSeconds)}</p>
          ) : null}

          {error.requestId ? (
            <p className="text-xs text-muted-foreground">
              {requestIdLabel}: <code className="font-mono">{error.requestId}</code>
            </p>
          ) : null}
        </div>

        <Button type="button" variant="secondary" onClick={onRetry} disabled={retrying} className="shrink-0">
          {retrying ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {retrying ? retryingLabel : retryLabel}
        </Button>
      </div>
    </div>
  );
}

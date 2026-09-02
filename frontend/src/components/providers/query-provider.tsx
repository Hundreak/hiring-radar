'use client';

import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {SessionExpiryBoundary} from '@/components/auth/session-expiry-boundary';
import {shouldRetryApiQuery} from '@/lib/api-error-ui';
import {useState} from 'react';

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry(failureCount, error) {
          if (!shouldRetryApiQuery(error)) {
            return false;
          }

          return failureCount < 1;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export function QueryProvider({children}: {children: React.ReactNode}) {
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <SessionExpiryBoundary />
    </QueryClientProvider>
  );
}

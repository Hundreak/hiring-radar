'use client';

import dynamic from 'next/dynamic';

const LazyCopilotWidget = dynamic(
  () => import('@/components/ai/copilot-widget').then((module) => module.CopilotWidget),
  {
    ssr: false,
    loading: () => (
      <div
        aria-hidden="true"
        className="fixed bottom-5 right-5 z-40 size-12 animate-pulse rounded-2xl border border-border bg-surface/90 shadow-lg"
      />
    ),
  }
);

export function CopilotWidgetLoader({locale}: {locale: string}) {
  return <LazyCopilotWidget locale={locale} />;
}

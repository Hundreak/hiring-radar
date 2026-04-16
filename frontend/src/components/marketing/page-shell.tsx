import type {ReactNode} from 'react';

import {PublicFooter} from '@/components/layout/public-footer';
import {PublicHeader} from '@/components/layout/public-header';

type MarketingPageShellProps = {
  locale: string;
  children: ReactNode;
};

export function MarketingPageShell({
  locale,
  children
}: MarketingPageShellProps) {
  return (
    <div className="min-h-screen bg-[#111111] text-white">
      <PublicHeader locale={locale} />
      <main>{children}</main>
      <PublicFooter locale={locale} />
    </div>
  );
}
import type {Metadata} from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'NoyTera',
  description:
    'NoyTera helps candidates structure their profile, discover better-fit roles and move through the hiring market with more clarity.'
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html suppressHydrationWarning data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
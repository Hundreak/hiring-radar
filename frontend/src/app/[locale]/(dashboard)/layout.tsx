import {AppShell} from '@/components/layout/app-shell';

export default async function DashboardLayout({
  children,
  params
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{locale: string}>;
}>) {
  const {locale} = await params;
  return <AppShell locale={locale}>{children}</AppShell>;
}

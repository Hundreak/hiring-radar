import {EmployerShell} from '@/components/employer/employer-shell';

type EmployerLayoutProps = Readonly<{
  children: React.ReactNode;
  params: Promise<{locale: string}>;
}>;

export default async function EmployerLayout({children, params}: EmployerLayoutProps) {
  const {locale} = await params;

  return <EmployerShell locale={locale}>{children}</EmployerShell>;
}

import {EmployerCockpit} from '@/components/employer/dashboard/employer-cockpit';

type EmployerDashboardPageProps = Readonly<{
  params: Promise<{locale: string}>;
}>;

export default async function EmployerDashboardPage({params}: EmployerDashboardPageProps) {
  const {locale} = await params;

  return <EmployerCockpit locale={locale} />;
}

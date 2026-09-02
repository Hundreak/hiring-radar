import {EmployerAnalyticsPage} from '@/components/employer/analytics/employer-analytics-page';

type EmployerAnalyticsRouteProps = {
  params: Promise<{locale: string}>;
};

export default async function EmployerAnalyticsRoute({params}: EmployerAnalyticsRouteProps) {
  const {locale} = await params;
  return <EmployerAnalyticsPage locale={locale} />;
}

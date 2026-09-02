import {EmployerComingSoonPage} from '@/components/employer/routes/employer-coming-soon-page';

export default async function EmployerInterviewsPage({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  return <EmployerComingSoonPage locale={locale} kind="interviews" />;
}

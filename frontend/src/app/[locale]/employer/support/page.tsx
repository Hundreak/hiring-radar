import {EmployerComingSoonPage} from '@/components/employer/routes/employer-coming-soon-page';

export default async function EmployerSupportPage({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  return <EmployerComingSoonPage locale={locale} kind="support" />;
}

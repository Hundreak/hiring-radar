import {EmployerCompliancePage} from '@/components/employer/compliance/employer-compliance-page';

export default async function EmployerComplianceRoute({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  return <EmployerCompliancePage locale={locale} />;
}

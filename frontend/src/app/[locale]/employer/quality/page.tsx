import {EmployerProductionQaPage} from '@/components/employer/quality/employer-production-qa-page';

export default async function EmployerQualityPage({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  return <EmployerProductionQaPage locale={locale} />;
}

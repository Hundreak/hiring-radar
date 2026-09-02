import {CompanyBrandPage} from '@/components/employer/company/company-brand-page';

type EmployerCompanyRouteProps = Readonly<{
  params: Promise<{locale: string}>;
}>;

export default async function EmployerCompanyRoute({params}: EmployerCompanyRouteProps) {
  const {locale} = await params;
  return <CompanyBrandPage locale={locale} />;
}

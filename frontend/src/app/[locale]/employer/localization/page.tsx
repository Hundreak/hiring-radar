import {EmployerLocalizationPage} from '@/components/employer/localization/employer-localization-page';

type EmployerLocalizationRouteProps = Readonly<{
  params: Promise<{locale: string}>;
}>;

export default async function EmployerLocalizationRoute({params}: EmployerLocalizationRouteProps) {
  const {locale} = await params;
  return <EmployerLocalizationPage locale={locale} />;
}

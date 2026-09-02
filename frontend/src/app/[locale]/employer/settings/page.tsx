import {EmployerSettingsPage} from '@/components/employer/settings/employer-settings-page';

type EmployerSettingsRouteProps = {
  params: Promise<{locale: string}>;
};

export default async function EmployerSettingsRoute({params}: EmployerSettingsRouteProps) {
  const {locale} = await params;
  return <EmployerSettingsPage locale={locale} />;
}

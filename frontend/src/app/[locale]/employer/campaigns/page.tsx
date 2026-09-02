import {OutreachCampaignsPage} from '@/components/employer/campaigns/outreach-campaigns-page';

type EmployerCampaignsRouteProps = Readonly<{
  params: Promise<{locale: string}>;
}>;

export default async function EmployerCampaignsRoute({params}: EmployerCampaignsRouteProps) {
  const {locale} = await params;

  return <OutreachCampaignsPage locale={locale} />;
}

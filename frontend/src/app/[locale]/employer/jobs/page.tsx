import { EmployerJobsPage } from "@/components/employer/jobs/employer-jobs-page";

type EmployerJobsRouteProps = Readonly<{
  params: Promise<{ locale: string }>;
}>;

export default async function EmployerJobsRoute({
  params,
}: EmployerJobsRouteProps) {
  const { locale } = await params;

  return <EmployerJobsPage locale={locale} />;
}

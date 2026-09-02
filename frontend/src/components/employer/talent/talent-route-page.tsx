import {TalentCommandCenter} from '@/components/employer/talent/talent-command-center';

export type TalentRouteSearchParams = Record<string, string | string[] | undefined>;

export type EmployerTalentRouteProps = Readonly<{
  params: Promise<{locale: string}>;
  searchParams?: Promise<TalentRouteSearchParams>;
}>;

type TalentView = 'pipeline' | 'compare' | 'outreach' | 'radar';
type TalentPanel = '360' | null;

function firstParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function parseTalentView(value: string | undefined): TalentView {
  return value === 'pipeline' || value === 'compare' || value === 'outreach' || value === 'radar'
    ? value
    : 'radar';
}

function parseCandidateId(value: string | undefined) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
}

function parseTalentPanel(value: string | undefined): TalentPanel {
  return value === '360' ? '360' : null;
}

export default async function EmployerTalentRoutePage({params, searchParams}: EmployerTalentRouteProps) {
  const {locale} = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const initialView = parseTalentView(firstParam(resolvedSearchParams.view));
  const initialCandidateId = parseCandidateId(firstParam(resolvedSearchParams.candidate));
  const initialPanel = parseTalentPanel(firstParam(resolvedSearchParams.panel));
  const routeKey = `${initialView}:${initialCandidateId ?? 'none'}:${initialPanel ?? 'none'}`;

  return (
    <TalentCommandCenter
      key={routeKey}
      locale={locale}
      initialView={initialView}
      initialCandidateId={initialCandidateId}
      initialPanel={initialPanel}
    />
  );
}

import {redirect} from 'next/navigation';

export default async function EmployerCandidateLegacyRedirect({
  params,
}: {
  params: Promise<{locale: string; id: string}>;
}) {
  const {locale, id} = await params;
  redirect(`/${locale}/employer/candidates?candidate=${encodeURIComponent(id)}&panel=360`);
}

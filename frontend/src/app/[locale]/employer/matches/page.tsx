import {redirect} from 'next/navigation';

export default async function EmployerMatchesLegacyRedirect({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  redirect(`/${locale}/employer/talent`);
}

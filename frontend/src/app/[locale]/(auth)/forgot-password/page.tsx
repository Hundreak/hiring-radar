import {ForgotPasswordView} from '@/components/auth/forgot-password-view';

export default async function ForgotPasswordPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <div className="min-h-screen bg-[#07090d] text-white">
      <ForgotPasswordView locale={locale} />
    </div>
  );
}
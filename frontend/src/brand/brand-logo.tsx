import Image from 'next/image';
import Link from 'next/link';

type BrandLogoSize = 'sm' | 'md' | 'lg';

type BrandLogoProps = {
  href?: string;
  size?: BrandLogoSize;
  className?: string;
  priority?: boolean;
  locale?: string;
  showSubtitle?: boolean;
};

const sizeClasses: Record<BrandLogoSize, string> = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12'
};

function BrandLogoInner({
  size = 'md',
  className,
  priority = false
}: Omit<BrandLogoProps, 'href'>) {
  return (
    <div className={`inline-flex items-center justify-center ${className ?? ''}`}>
      <div className={`relative shrink-0 ${sizeClasses[size]}`}>
        <Image
          src="/brand/noytera-logo.png"
          alt="NoyTera logo"
          width={256}
          height={256}
          priority={priority}
          sizes={size === 'sm' ? '32px' : size === 'md' ? '40px' : '48px'}
          className="h-auto w-full select-none object-contain"
          draggable={false}
        />
      </div>
    </div>
  );
}

export function BrandLogo(props: BrandLogoProps) {
  const {href} = props;

  if (!href) {
    return <BrandLogoInner {...props} />;
  }

  return (
    <Link
      href={href}
      aria-label="NoyTera home"
      className="inline-flex items-center justify-center"
    >
      <BrandLogoInner {...props} />
    </Link>
  );
}

export default BrandLogo;
'use client';

import Link from 'next/link';
import {Sparkles} from 'lucide-react';

type BrandLogoProps = {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  locale?: string;
  className?: string;
  priority?: boolean;
  asLink?: boolean;
};

const iconSizeClass = {
  sm: 'h-7 w-7 rounded-lg',
  md: 'h-8 w-8 rounded-lg',
  lg: 'h-10 w-10 rounded-2xl'
} as const;

const iconGlyphSizeClass = {
  sm: 'size-3.5',
  md: 'size-4',
  lg: 'size-5'
} as const;

const titleSizeClass = {
  sm: 'text-base',
  md: 'text-lg',
  lg: 'text-xl'
} as const;

export function BrandLogo({
  size = 'md',
  showSubtitle = true,
  locale = 'tr',
  className,
  asLink = true
}: BrandLogoProps) {
  const content = (
    <>
      <div className={`flex items-center justify-center bg-primary text-primary-foreground ${iconSizeClass[size]}`}>
        <Sparkles className={iconGlyphSizeClass[size]} />
      </div>
      {showSubtitle && (
        <div className="min-w-0">
          <div className={`truncate font-semibold leading-none tracking-tight text-foreground ${titleSizeClass[size]}`}>
            NoyTera
          </div>
          <div className="mt-0.5 truncate text-[11px] leading-none text-muted-foreground">
            AI destekli kariyer platformu
          </div>
        </div>
      )}
    </>
  );

  const classes = `inline-flex items-center gap-2 ${className || ''}`;

  if (!asLink) {
    return <span className={classes}>{content}</span>;
  }

  return (
    <Link href={`/${locale}`} className={classes} aria-label="NoyTera home">
      {content}
    </Link>
  );
}

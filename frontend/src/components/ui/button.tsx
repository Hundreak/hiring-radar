import {cva, type VariantProps} from 'class-variance-authority';

import {cn} from '@/lib/utils';

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-bold tracking-[-0.01em]',
    'min-h-10 cursor-pointer select-none whitespace-nowrap transition-[transform,background-color,border-color,color,box-shadow,opacity] duration-150 ease-out',
    'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
    'active:translate-y-[1px] active:scale-[0.985] disabled:pointer-events-none disabled:opacity-55'
  ].join(' '),
  {
    variants: {
      variant: {
        primary:
          'border border-primary/20 bg-primary text-primary-foreground shadow-[0_12px_28px_color-mix(in_srgb,var(--primary)_24%,transparent)] hover:-translate-y-0.5 hover:shadow-[0_16px_36px_color-mix(in_srgb,var(--primary)_30%,transparent)]',
        secondary:
          'border border-border bg-surface-elevated text-foreground shadow-sm hover:-translate-y-0.5 hover:border-primary/35 hover:bg-surface-strong',
        ghost:
          'bg-transparent text-muted-foreground hover:bg-surface-muted hover:text-foreground',
        outline:
          'border border-border bg-transparent text-foreground hover:-translate-y-0.5 hover:border-primary/40 hover:bg-surface-muted',
        soft:
          'border border-primary/15 bg-secondary text-secondary-foreground hover:-translate-y-0.5 hover:border-primary/35 hover:bg-primary/20',
        danger:
          'border border-red-500/20 bg-red-500/10 text-danger hover:-translate-y-0.5 hover:bg-red-500/15'
      },
      size: {
        sm: 'h-9 px-3.5 py-2 text-xs',
        md: 'h-10 px-4 py-2.5',
        lg: 'h-12 px-5 py-3 text-sm',
        xl: 'h-[52px] px-6 py-3.5 text-base'
      }
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md'
    }
  }
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({className, variant, size, ...props}: ButtonProps) {
  return <button className={cn(buttonVariants({variant, size}), className)} {...props} />;
}

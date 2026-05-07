import {cva, type VariantProps} from 'class-variance-authority';

import {cn} from '@/lib/utils';

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center rounded-2xl text-sm font-semibold',
    'cursor-pointer select-none transition-[transform,background-color,border-color,color,box-shadow,opacity] duration-150 ease-out',
    'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
    'active:translate-y-[1px] active:scale-[0.985] disabled:pointer-events-none disabled:opacity-60'
  ].join(' '),
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:opacity-95 shadow-sm',
        secondary:
          'border border-border bg-surface text-foreground hover:border-primary/40 hover:bg-surface-muted',
        ghost:
          'bg-transparent text-muted-foreground hover:bg-surface-muted hover:text-foreground',
        outline:
          'border border-border bg-transparent text-foreground hover:border-primary/40 hover:bg-surface-muted'
      },
      size: {
        sm: 'h-9 px-3.5 py-2 text-xs',
        md: 'px-4 py-2.5',
        lg: 'h-11 px-5 py-3 text-sm'
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

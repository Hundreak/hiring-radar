import {cn} from '@/lib/utils';

export function IconButton({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        'inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/40 hover:text-foreground',
        className
      )}
      {...props}
    />
  );
}

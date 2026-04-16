import {cn} from '@/lib/utils';

export function Badge({
  className,
  tone = 'default',
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  tone?: 'default' | 'accent' | 'success' | 'warning' | 'danger' | 'info' | 'matched' | 'missing' | 'remote' | 'new';
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold',
        tone === 'default' && 'bg-surface-muted text-muted-foreground',
        tone === 'accent' && 'bg-accent-soft text-accent',
        tone === 'success' && 'bg-emerald-500/10 text-success',
        tone === 'warning' && 'bg-amber-500/10 text-warning',
        tone === 'danger' && 'bg-red-500/10 text-danger',
        tone === 'info' && 'bg-blue-500/10 text-blue-500',
        tone === 'matched' && 'bg-[rgba(39,80,10,0.2)] text-[#27500A] dark:text-[#6bba30]',
        tone === 'missing' && 'bg-[rgba(121,31,31,0.2)] text-[#791F1F] dark:text-[#e87070]',
        tone === 'remote' && 'bg-[rgba(99,56,6,0.2)] text-[#633806] dark:text-[#EF9F27]',
        tone === 'new' && 'bg-[rgba(24,95,165,0.15)] text-[#185FA5] dark:text-[#60a5fa]',
        className
      )}
      {...props}
    />
  );
}

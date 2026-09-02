import type React from 'react';
import type {ReactNode} from 'react';

import type {ProfileWorkspaceCopy as Copy} from '@/components/profile/profile-workspace-copy';

export function Surface({children}: {children: ReactNode}) {
  return <section className="rounded-[28px] border border-border bg-background p-6 shadow-[0_14px_45px_-28px_rgba(15,23,42,0.24)] sm:p-7">{children}</section>;
}

export function SectionHeader({title, body, action}: {title: string; body?: string; action?: ReactNode}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">{title}</h2>
        {body ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{body}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function InputField(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`h-12 w-full rounded-2xl border border-border bg-background px-4 text-sm text-foreground outline-none transition focus:border-foreground/25 focus:ring-4 focus:ring-primary/10 ${props.className ?? ''}`} />;
}

export function TextAreaField(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`min-h-[120px] w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition focus:border-foreground/25 focus:ring-4 focus:ring-primary/10 ${props.className ?? ''}`} />;
}

export function SelectField(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`h-12 w-full rounded-2xl border border-border bg-background px-4 text-sm text-foreground outline-none transition focus:border-foreground/25 focus:ring-4 focus:ring-primary/10 ${props.className ?? ''}`} />;
}

export function PrimaryButton({children, type = 'button', ...props}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type={type} {...props} className={`inline-flex h-11 items-center justify-center rounded-2xl bg-foreground px-5 text-sm font-medium text-background transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60 ${props.className ?? ''}`}>{children}</button>;
}

export function SecondaryButton({children, danger = false, type = 'button', ...props}: React.ButtonHTMLAttributes<HTMLButtonElement> & {danger?: boolean}) {
  return (
    <button
      type={type}
      {...props}
      className={`inline-flex h-11 items-center justify-center rounded-2xl border px-5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${danger ? 'border-rose-200 text-rose-600 hover:bg-rose-50' : 'border-border bg-background text-foreground hover:bg-muted/50'} ${props.className ?? ''}`}
    >
      {children}
    </button>
  );
}

export function Chip({children}: {children: ReactNode}) {
  return <span className="inline-flex items-center rounded-full border border-border bg-muted/20 px-3 py-1 text-xs font-medium text-foreground">{children}</span>;
}


export function LoadingView({copy}: {copy: Copy}) {
  return (
    <div className="rounded-[28px] border border-border bg-background p-8">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">{copy.loadingTitle}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{copy.loadingBody}</p>
    </div>
  );
}




export function Field({label, hint, marker, children}: {label: string; hint?: string; marker?: ReactNode; children: ReactNode}) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-medium text-foreground">{label}</div>
        {marker}
      </div>
      {children}
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function EmptyState({children}: {children: ReactNode}) {
  return <div className="rounded-2xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">{children}</div>;
}

export function OverviewCard({title, children, className = ''}: {title: string; children: ReactNode; className?: string}) {
  return (
    <div className={`rounded-2xl border border-border bg-muted/20 p-4 ${className}`}>
      <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</div>
      <div className="mt-2 text-sm leading-7 text-foreground">{children}</div>
    </div>
  );
}

export function OverviewListCard({title, items, emptyLabel}: {title: string; items: string[]; emptyLabel: string}) {
  return (
    <div className="rounded-2xl border border-border bg-muted/20 p-4">
      <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length > 0 ? items.map((item) => <Chip key={item}>{item}</Chip>) : <span className="text-sm text-muted-foreground">{emptyLabel}</span>}
      </div>
    </div>
  );
}

export function EditorCard({children}: {children: ReactNode}) {
  return <div className="rounded-[22px] border border-dashed border-border bg-muted/10 p-5">{children}</div>;
}

export function EditorActions({onSave, onCancel, busy, saveLabel, t}: {onSave: () => void; onCancel: () => void; busy: boolean; saveLabel: string; t: Copy}) {
  return (
    <div className="mt-5 flex flex-wrap gap-3">
      <PrimaryButton onClick={onSave} disabled={busy}>{busy ? t.saving : saveLabel}</PrimaryButton>
      <SecondaryButton onClick={onCancel} disabled={busy}>{t.cancel}</SecondaryButton>
    </div>
  );
}

export function EntityCard({icon, title, subtitle, description, chips = [], onEdit, onDelete, deleting, t}: {icon: ReactNode; title: string; subtitle: string; description?: string; chips?: string[]; onEdit: () => void; onDelete?: () => void; deleting: boolean; t: Copy}) {
  return (
    <article className="rounded-[22px] border border-border bg-muted/15 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-foreground">
            <span className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-background">{icon}</span>
            <div>
              <div className="text-base font-semibold text-foreground">{title}</div>
              <div className="text-sm text-muted-foreground">{subtitle}</div>
            </div>
          </div>
          {description ? <p className="text-sm leading-7 text-muted-foreground">{description}</p> : null}
          {chips.length > 0 ? <div className="flex flex-wrap gap-2">{chips.map((item) => <Chip key={item}>{item}</Chip>)}</div> : null}
        </div>
        <div className="flex gap-3">
          <SecondaryButton onClick={onEdit}>{t.edit}</SecondaryButton>
          {onDelete ? <SecondaryButton onClick={onDelete} danger disabled={deleting}>{deleting ? t.deleting : t.delete}</SecondaryButton> : null}
        </div>
      </div>
    </article>
  );
}

'use client';

import {Building2, Check, ChevronDown, ShieldCheck} from 'lucide-react';
import {useMemo, useState} from 'react';

import {getEmployerCopy} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';

export function CompanySwitcher({locale}: {locale: string}) {
  const copy = useMemo(() => getEmployerCopy(locale), [locale]);
  const companies = copy.companySwitcher.companies;
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(companies[0]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className={cn(
          'group flex w-full items-center gap-3 rounded-3xl border border-border bg-surface-elevated/80 p-3 text-left shadow-sm transition',
          'hover:border-primary/35 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]'
        )}
        aria-expanded={isOpen}
      >
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-sm font-black text-white shadow-lg shadow-primary/10">
          {selectedCompany.initials}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-sm font-bold text-foreground">{selectedCompany.name}</span>
            {selectedCompany.verified ? (
              <ShieldCheck className="size-3.5 shrink-0 text-success" aria-label={copy.companySwitcher.verifiedCompany} />
            ) : null}
          </div>
          <p className="truncate text-[11px] font-medium text-muted-foreground">{selectedCompany.plan}</p>
        </div>
        <ChevronDown className={cn('size-4 shrink-0 text-muted-foreground transition', isOpen && 'rotate-180')} />
      </button>

      {isOpen ? (
        <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-50 overflow-hidden rounded-3xl border border-border bg-surface-elevated shadow-2xl shadow-black/30">
          <div className="border-b border-border px-3 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            {copy.companySwitcher.workspace}
          </div>
          <div className="p-2">
            {companies.map((company) => {
              const isSelected = company.id === selectedCompany.id;
              return (
                <button
                  key={company.id}
                  type="button"
                  onClick={() => {
                    setSelectedCompany(company);
                    setIsOpen(false);
                  }}
                  className={cn(
                    'flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition',
                    'hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
                    isSelected && 'bg-secondary text-secondary-foreground'
                  )}
                >
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-surface-muted text-xs font-black text-foreground">
                    {company.initials || <Building2 className="size-4" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-foreground">{company.name}</div>
                    <div className="truncate text-[11px] text-muted-foreground">{company.plan}</div>
                  </div>
                  {isSelected ? <Check className="size-4 text-primary" /> : null}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

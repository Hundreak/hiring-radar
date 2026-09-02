'use client';

import {useEffect, useMemo, useRef, useState} from 'react';
import {Check, ChevronDown, Search} from 'lucide-react';

import {cn} from '@/lib/utils';

type ComboboxOption = {
  value: string;
  label: string;
  hint?: string | null;
};

type ComboboxFieldProps = {
  value: string;
  onChange: (value: string) => void;
  options: ComboboxOption[];
  placeholder?: string;
  emptyLabel?: string;
  disabled?: boolean;
};

export function ComboboxField({
  value,
  onChange,
  options,
  placeholder = 'Seç veya yaz',
  emptyLabel = 'Eşleşme bulunamadı.',
  disabled = false,
}: ComboboxFieldProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  const normalizedValue = value.trim().toLocaleLowerCase('tr-TR');

  const selectedOption = useMemo(
    () => options.find((option) => option.value.trim().toLocaleLowerCase('tr-TR') === normalizedValue) ?? null,
    [normalizedValue, options],
  );

  const filteredOptions = useMemo(() => {
    const keyword = query.trim().toLocaleLowerCase('tr-TR');
    if (!keyword) {
      return options.slice(0, 12);
    }

    return options
      .filter((option) => {
        const haystack = [option.label, option.value, option.hint ?? '']
          .join(' ')
          .toLocaleLowerCase('tr-TR');
        return haystack.includes(keyword);
      })
      .slice(0, 12);
  }, [options, query]);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={open ? query : value}
            disabled={disabled}
            placeholder={placeholder}
            onFocus={() => {
              setOpen(true);
              setQuery(value);
            }}
            onChange={(event) => {
              const nextValue = event.target.value;
              setQuery(nextValue);
              onChange(nextValue);
              setOpen(true);
            }}
            className="h-12 w-full rounded-2xl border border-border bg-background pl-10 pr-4 text-sm text-foreground outline-none transition focus:border-foreground/30 focus:ring-4 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
          />
        </div>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((current) => !current)}
          className="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-background text-muted-foreground transition hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60"
          aria-label="Seçenekleri aç"
        >
          <ChevronDown className={cn('size-4 transition-transform', open ? 'rotate-180' : '')} />
        </button>
      </div>

      {open ? (
        <div className="absolute z-30 mt-2 max-h-72 w-full overflow-y-auto rounded-3xl border border-border bg-background p-2 shadow-[0_20px_70px_-30px_rgba(15,23,42,0.45)]">
          {filteredOptions.length > 0 ? (
            <div className="space-y-1">
              {filteredOptions.map((option) => {
                const selected = option.value.trim().toLocaleLowerCase('tr-TR') === normalizedValue;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onChange(option.value);
                      setQuery(option.label);
                      setOpen(false);
                    }}
                    className={cn(
                      'flex w-full items-start justify-between gap-3 rounded-2xl px-4 py-3 text-left transition',
                      selected ? 'bg-foreground text-background' : 'hover:bg-muted/50 text-foreground',
                    )}
                  >
                    <span>
                      <span className="block text-sm font-medium">{option.label}</span>
                      {option.hint ? (
                        <span className={cn('mt-1 block text-xs', selected ? 'text-background/75' : 'text-muted-foreground')}>
                          {option.hint}
                        </span>
                      ) : null}
                    </span>
                    {selected ? <Check className="mt-0.5 size-4 shrink-0" /> : null}
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
              {emptyLabel}
            </div>
          )}
        </div>
      ) : null}

      {selectedOption?.hint ? (
        <p className="mt-2 text-xs text-muted-foreground">{selectedOption.hint}</p>
      ) : null}
    </div>
  );
}

export type {ComboboxOption};

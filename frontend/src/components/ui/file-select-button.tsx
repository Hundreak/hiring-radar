'use client';

import {useId, useRef} from 'react';
import {Paperclip, Upload} from 'lucide-react';

export function FileSelectButton({
  label,
  accept,
  file,
  buttonLabel,
  emptyLabel,
  onChange,
}: {
  label: string;
  accept?: string;
  file: File | null;
  buttonLabel: string;
  emptyLabel?: string;
  onChange: (file: File | null) => void;
}) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-foreground">{label}</div>
      <input
        id={inputId}
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(event) => {
          const nextFile = event.target.files?.[0] ?? null;
          onChange(nextFile);
          event.currentTarget.value = '';
        }}
      />
      <div className="flex flex-col gap-3 rounded-2xl border border-border bg-muted/10 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-2xl border border-border bg-background text-muted-foreground">
            <Paperclip className="size-4" />
          </span>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-foreground">
              {file?.name || emptyLabel || 'Henüz dosya seçilmedi'}
            </div>
            {file ? (
              <div className="mt-1 text-xs text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </div>
            ) : null}
          </div>
        </div>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="inline-flex h-11 shrink-0 items-center justify-center rounded-2xl border border-border bg-background px-5 text-sm font-medium text-foreground transition hover:bg-muted/50"
        >
          <Upload className="mr-2 size-4" />
          {buttonLabel}
        </button>
      </div>
    </div>
  );
}

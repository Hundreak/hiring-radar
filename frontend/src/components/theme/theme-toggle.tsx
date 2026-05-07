'use client';

import {useState} from 'react';
import {Moon, Sun, Flame, Crown, ChevronDown} from 'lucide-react';

import {useTheme, type Theme} from '@/components/theme/theme-provider';
import {cn} from '@/lib/utils';

/* ── Theme definitions ── */
interface ThemeOption {
  id: Theme;
  label: string;
  description: string;
  icon: React.ReactNode;
  colorClass: string; /* dot color indicator */
}

const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'obsidian',
    label: 'Obsidian',
    description: 'Ultra-premium dark',
    icon: <Moon className="size-4" />,
    colorClass: 'bg-[#6366F1]'
  },
  {
    id: 'platinum',
    label: 'Platinum',
    description: 'Clean investor-grade',
    icon: <Sun className="size-4" />,
    colorClass: 'bg-[#64748b]'
  },
  {
    id: 'crimson',
    label: 'Crimson',
    description: 'Bold & energetic',
    icon: <Flame className="size-4" />,
    colorClass: 'bg-[#DC2626]'
  },
  {
    id: 'aurum',
    label: 'Aurum',
    description: 'Gold luxury',
    icon: <Crown className="size-4" />,
    colorClass: 'bg-[#D4AF37]'
  }
];

export function ThemeToggle() {
  const {resolvedTheme, setTheme} = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  const activeOption = THEME_OPTIONS.find((t) => t.id === resolvedTheme) ?? THEME_OPTIONS[0];

  return (
    <div className="relative">
      {/* ── Trigger Button ── */}
      <button
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Select theme"
        className={cn(
          'inline-flex items-center gap-2 rounded-2xl border border-border bg-surface',
          'px-3 py-2.5 text-muted-foreground transition-all duration-200',
          'hover:border-primary/40 hover:text-foreground',
          'focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2',
          isOpen && 'border-primary/40 text-foreground'
        )}
        onClick={() => setIsOpen((prev) => !prev)}
        type="button"
      >
        <span className="flex items-center justify-center text-foreground">
          {activeOption.icon}
        </span>
        <span className="hidden text-sm font-medium text-foreground sm:inline">
          {activeOption.label}
        </span>
        <ChevronDown
          className={cn(
            'size-3.5 text-muted-foreground transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* ── Dropdown Menu ── */}
      {isOpen && (
        <>
          {/* Backdrop to close on outside click */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          <div
            className={cn(
              'absolute right-0 top-full z-50 mt-2 w-56',
              'rounded-2xl border border-border bg-surface-elevated',
              'p-1.5 shadow-lg animate-scale-in'
            )}
            role="listbox"
          >
            <div className="px-3 py-2">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Theme
              </p>
            </div>

            <div className="flex flex-col gap-0.5">
              {THEME_OPTIONS.map((option) => {
                const isActive = option.id === resolvedTheme;
                return (
                  <button
                    key={option.id}
                    className={cn(
                      'flex items-center gap-3 rounded-xl px-3 py-2.5 text-left',
                      'transition-all duration-150',
                      isActive
                        ? 'bg-primary/10 text-foreground'
                        : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'
                    )}
                    onClick={() => {
                      setTheme(option.id);
                      setIsOpen(false);
                    }}
                    role="option"
                    aria-selected={isActive}
                    type="button"
                  >
                    {/* Icon */}
                    <span
                      className={cn(
                        'flex size-8 shrink-0 items-center justify-center rounded-lg',
                        isActive ? 'bg-primary/15 text-primary' : 'bg-surface-muted text-muted-foreground'
                      )}
                    >
                      {option.icon}
                    </span>

                    {/* Label + description */}
                    <div className="flex min-w-0 flex-1 flex-col">
                      <span className="text-sm font-medium">
                        {option.label}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">
                        {option.description}
                      </span>
                    </div>

                    {/* Active indicator dot */}
                    <span
                      className={cn(
                        'size-2 rounded-full transition-transform',
                        option.colorClass,
                        isActive ? 'scale-100' : 'scale-0'
                      )}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

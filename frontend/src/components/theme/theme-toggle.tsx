'use client';

import { useEffect, useState, useSyncExternalStore } from 'react';
import { Crown, Eye, Flame, Moon, Sun } from 'lucide-react';
import { useTheme, type Theme } from './theme-provider';

function subscribe() { return () => {}; }
function useIsHydrated() { return useSyncExternalStore(subscribe, () => true, () => false); }

const themeOptions: Array<{ id: Theme; label: string; description: string; icon: React.ElementType; dot: string }> = [
  { id: 'clarity', label: 'Clarity', description: 'En rahat okunabilir tema', icon: Eye, dot: 'bg-[#37d6c3]' },
  { id: 'obsidian', label: 'Obsidian', description: 'Premium koyu tema', icon: Moon, dot: 'bg-[#6366F1]' },
  { id: 'platinum', label: 'Platinum', description: 'Temiz açık tema', icon: Sun, dot: 'bg-[#64748b]' },
  { id: 'crimson', label: 'Crimson', description: 'Enerjik koyu tema', icon: Flame, dot: 'bg-[#DC2626]' },
  { id: 'aurum', label: 'Aurum', description: 'Altın flagship tema', icon: Crown, dot: 'bg-[#D4AF37]' },
];

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isHydrated = useIsHydrated();
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    if (!showMenu) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setShowMenu(false);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [showMenu]);

  if (!isHydrated) {
    return <div className="h-9 w-9 rounded-xl border border-border bg-surface-muted" />;
  }

  const currentOption = themeOptions.find(t => t.id === resolvedTheme) || themeOptions[0];
  const Icon = currentOption.icon;

  return (
    <div className="relative">
      <button
        aria-label="Tema seç"
        aria-haspopup="menu"
        aria-expanded={showMenu}
        onClick={() => setShowMenu(!showMenu)}
        className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-surface-muted text-foreground shadow-sm transition hover:border-primary/40 hover:bg-surface-strong focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
        type="button"
      >
        <Icon className="size-4" />
      </button>
      {showMenu && (
        <>
          <button className="fixed inset-0 z-40 cursor-default" aria-label="Tema menüsünü kapat" onClick={() => setShowMenu(false)} type="button" />
          <div className="absolute right-0 top-10 z-50 w-60 rounded-2xl border border-border bg-surface-elevated p-2 shadow-lg">
            <div className="px-3 py-2 text-[11px] font-black uppercase tracking-[0.18em] text-muted-foreground">Tema</div>
            {themeOptions.map(opt => {
              const OptIcon = opt.icon;
              const active = resolvedTheme === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => { setTheme(opt.id); setShowMenu(false); }}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${active ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'}`}
                  role="menuitemradio"
                  aria-checked={active}
                  type="button"
                >
                  <span className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${active ? 'bg-primary/15 text-primary' : 'bg-surface-muted text-muted-foreground'}`}>
                    <OptIcon className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold">{opt.label}</span>
                    <span className="block truncate text-xs opacity-75">{opt.description}</span>
                  </span>
                  <span className={`size-2 rounded-full ${opt.dot} ${active ? 'opacity-100' : 'opacity-30'}`} />
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

'use client';
import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/cn';

// One-off, chapter-scoped state: unlike lib/progress.ts's shared Progress
// object, nothing outside this component ever reads a migration checklist,
// so a small localStorage entry of its own is simpler than growing the
// shared schema for a single chapter.
const KEY = 'z2oe-migration-checklist';

export interface MigrationChecklistItem {
  id: string;
  label: string;
}

export function MigrationChecklist({ items }: { items: MigrationChecklistItem[] }) {
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setChecked(JSON.parse(localStorage.getItem(KEY) ?? '{}'));
    } catch {
      setChecked({});
    }
    setReady(true);
  }, []);

  function toggle(id: string) {
    setChecked((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  }

  const done = items.filter((item) => checked[item.id]).length;

  return (
    <div className="not-prose rounded-lg border p-4">
      <p className="mb-3 text-sm font-medium text-fd-muted-foreground">
        {ready ? `${done} / ${items.length} done` : ' '}
      </p>
      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => toggle(item.id)}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-md border px-3 py-2 text-start text-sm transition-colors',
                checked[item.id]
                  ? 'border-green-500/40 bg-green-500/10 text-fd-muted-foreground line-through'
                  : 'cursor-pointer hover:border-fd-primary hover:bg-fd-accent',
              )}
            >
              <span
                className={cn(
                  'flex size-4 shrink-0 items-center justify-center rounded border',
                  checked[item.id]
                    ? 'border-green-500 bg-green-500 text-white'
                    : 'border-fd-muted-foreground/40',
                )}
              >
                {checked[item.id] && <Check className="size-3" />}
              </span>
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

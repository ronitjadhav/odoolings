'use client';
import { usePathname } from 'next/navigation';
import { CheckCircle2, Circle } from 'lucide-react';
import { cn } from '@/lib/cn';
import { chapterIdFromUrl, toggleDone, useProgress } from '@/lib/progress';

export function MarkComplete() {
  const pathname = usePathname();
  const progress = useProgress();
  const chapter = chapterIdFromUrl(pathname);
  if (!chapter || !progress) return null;

  const done = !!progress.done[chapter];
  return (
    <button
      type="button"
      onClick={() => toggleDone(chapter)}
      aria-pressed={done}
      className={cn(
        'mt-8 flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors cursor-pointer',
        done
          ? 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400'
          : 'hover:border-fd-primary hover:bg-fd-accent',
      )}
    >
      {done ? <CheckCircle2 className="size-4" /> : <Circle className="size-4" />}
      {done ? 'Chapter complete' : 'Mark chapter complete'}
    </button>
  );
}

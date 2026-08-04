'use client';
import { useEffect } from 'react';
import Link from 'next/link';
import { Flame } from 'lucide-react';
import { recordVisit, streak, useProgress } from '@/lib/progress';
import { TOTAL_CHAPTERS } from '@/lib/shared';

export function ProgressPill() {
  const progress = useProgress();
  useEffect(recordVisit, []);
  if (!progress) return null;

  const done = Object.keys(progress.done).length;
  const s = streak(progress.days);
  const pct = Math.round((done / TOTAL_CHAPTERS) * 100);

  return (
    <Link
      href="/docs"
      className="right-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-40 hidden items-center gap-2 rounded-full border bg-fd-background/90 px-3 py-1.5 text-xs font-medium shadow-lg backdrop-blur transition-colors hover:bg-fd-accent sm:fixed sm:flex"
      title={`${done} of ${TOTAL_CHAPTERS} chapters complete, see the full breakdown`}
      aria-label={`${done} of ${TOTAL_CHAPTERS} chapters complete. View progress.`}
    >
      <span
        className="relative hidden h-1.5 w-16 overflow-hidden rounded-full bg-fd-muted sm:block"
        role="progressbar"
        aria-label="Chapters completed"
        aria-valuemin={0}
        aria-valuemax={TOTAL_CHAPTERS}
        aria-valuenow={done}
      >
        <span
          className="absolute inset-y-0 left-0 rounded-full bg-fd-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </span>
      {done}/{TOTAL_CHAPTERS}
      {s > 1 && (
        <span className="flex items-center gap-0.5 text-orange-500">
          <Flame className="size-3.5" />
          {s}
        </span>
      )}
    </Link>
  );
}

'use client';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { useProgress } from '@/lib/progress';

export interface ChapterLink {
  id: string;
  url: string;
  title: string;
}

// Renders "Start learning" for first-time visitors. Once localStorage shows
// completed chapters, switches to the first one not yet done. progress is
// null on the server and on first paint, so SSG markup never mismatches; the
// swap happens after hydration.
export function HeroCta({ chapters }: { chapters: ChapterLink[] }) {
  const progress = useProgress();
  const done = progress?.done ?? {};
  const next = chapters.find((c) => !done[c.id]);
  const resuming = Boolean(progress && Object.keys(done).length > 0 && next);
  // Chapter titles are already "NN. Title" (see the write-chapter skill's
  // frontmatter template); strip the repeated number for this inline label.
  const nextTitle = next?.title.replace(/^\d+\.\s*/, '');

  return (
    <Link
      href={resuming && next ? next.url : '/docs'}
      className="group flex items-center gap-2 rounded-full bg-fd-primary px-6 py-3 font-medium text-fd-primary-foreground transition-all duration-300 ease-(--ease-out-soft) hover:shadow-(--shadow-card)"
    >
      {resuming && next ? `Continue: ${nextTitle}` : 'Start learning'}
      <ArrowRight className="size-4 transition-transform duration-300 ease-(--ease-out-soft) group-hover:translate-x-0.5" />
    </Link>
  );
}

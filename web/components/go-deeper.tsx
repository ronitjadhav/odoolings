import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { chapterIdFromUrl } from '@/lib/chapter-id';
import { GO_DEEPER, trackOf } from '@/lib/deep-dives';
import { source } from '@/lib/source';
import { Icon } from './icon';

/**
 * "Go deeper" card at the end of a journey chapter: the deep-dive chapters on the same
 * topic. Written ones link; planned ones are named so the reader knows depth is coming.
 */
export function GoDeeper({ chapter }: { chapter: string }) {
  const ids = GO_DEEPER[chapter];
  if (!ids?.length) return null;
  const track = trackOf(ids[0]);
  if (!track) return null;

  const written = new Map<string, { url: string; title: string }>();
  for (const page of source.getPages()) {
    const id = chapterIdFromUrl(page.url);
    if (id && ids.includes(id)) written.set(id, { url: page.url, title: page.data.title });
  }
  const entry = [...written.values()].find((p) => chapterIdFromUrl(p.url) === track.entry)
    ?? (() => {
      const page = source.getPages().find((p) => chapterIdFromUrl(p.url) === track.entry);
      return page ? { url: page.url, title: page.data.title } : null;
    })();

  return (
    <aside className="my-8 rounded-2xl border bg-(--tone-sage) p-5 text-sm">
      <p className="eyebrow text-fd-muted-foreground">Go deeper</p>
      <h2 className="mt-2 text-base font-semibold text-fd-foreground">
        This topic has its own deep dive: {track.name}
      </h2>
      <p className="mt-1 text-fd-muted-foreground">
        One pass here, every option there, in the simplest words we have. The deep dive
        runs on its own database, so you can jump in without finishing this part.
      </p>
      <ul className="mt-4 space-y-2">
        {ids.map((id) => {
          const page = written.get(id);
          const number = Number(id.replace(/^\D+/, ''));
          return (
            <li key={id} className="flex items-start gap-2">
              <span className="mt-0.5 w-28 shrink-0 whitespace-nowrap text-xs font-medium uppercase tracking-wider text-fd-muted-foreground">
                {track.name} {number}
              </span>
              {page ? (
                <Link
                  href={page.url}
                  className="group inline-flex items-center gap-1 font-medium text-fd-primary underline-offset-2 hover:underline"
                >
                  {page.title.replace(/^[A-Za-z]+ \d+\.\s*/, '')}
                  <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                </Link>
              ) : (
                <span className="text-fd-muted-foreground">
                  {track.chapters[id]} <span className="text-xs">(coming)</span>
                </span>
              )}
            </li>
          );
        })}
      </ul>
      {entry && !ids.includes(track.entry) ? (
        <p className="mt-4 text-fd-muted-foreground">
          New to {track.name}? <Icon name="learn" />{' '}
          <Link href={entry.url} className="font-medium text-fd-primary underline-offset-2 hover:underline">
            Start the deep dive from its first chapter
          </Link>
          .
        </p>
      ) : null}
    </aside>
  );
}

/**
 * The chapter number a docs URL refers to, or null if it isn't a chapter page.
 *
 * A chapter lives inside a part folder, so both the page AND its parent must
 * look like "NN-slug". Matching only the last segment would treat a part's own
 * index page (/docs/02-first-module) as chapter "02", which is a real chapter
 * belonging to a different part. Ignores any basePath prefix.
 *
 * Lives outside progress.ts (a 'use client' module) so server components, like
 * the homepage building its chapter list from `source.getPages()`, can import
 * it too.
 */
export function chapterIdFromUrl(url: string): string | null {
  const parts = url.split('/').filter(Boolean);
  if (parts.length < 2) return null;
  const [parent, last] = parts.slice(-2);
  if (!/^\d{2}-/.test(parent)) return null;
  // "09" for the journey; "inv01" for a deep-dive track (its own numbering, never 56+)
  return last.match(/^(\d{2}|[a-z]{2,4}\d{2})-/)?.[1] ?? null;
}

/** True for a journey chapter id ("09"), false for a track id ("inv01"). */
export function isJourneyChapter(id: string): boolean {
  return /^\d{2}$/.test(id);
}

/** The tier a journey chapter belongs to, from its Part folder; tracks declare theirs. */
export function tierFromUrl(url: string): 'foundations' | 'professional' | 'expert' | null {
  const parent = url.split('/').filter(Boolean).slice(-2)[0] ?? '';
  const part = Number(parent.match(/^(\d{2})-/)?.[1]);
  if (Number.isNaN(part)) return null;
  if (part <= 3) return 'foundations';
  if (part <= 7) return 'professional';
  if (part <= 9) return 'expert';
  return null;
}

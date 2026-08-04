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
  return last.match(/^(\d{2})-/)?.[1] ?? null;
}

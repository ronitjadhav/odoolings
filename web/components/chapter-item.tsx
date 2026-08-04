'use client';
import { usePathname } from 'next/navigation';
import { SidebarItem, useFolderDepth } from 'fumadocs-ui/components/sidebar/base';
import type * as PageTree from 'fumadocs-core/page-tree';
import { Check, ClipboardCheck, Trophy } from 'lucide-react';
import { cn } from '@/lib/cn';
import { chapterIdFromUrl, useProgress } from '@/lib/progress';

// These classes mirror fumadocs' internal `itemVariants` from
// layouts/docs/slots/sidebar. That styled SidebarItem is not exported, so
// overriding the Item slot means re-applying it by hand. Re-check on upgrade.
const ITEM_BASE =
  'relative flex flex-row items-start gap-2 rounded-lg p-2 text-start ' +
  'text-fd-muted-foreground wrap-anywhere transition-colors ' +
  'hover:bg-fd-accent/50 hover:text-fd-accent-foreground/80 hover:transition-none ' +
  'data-[active=true]:bg-fd-primary/10 data-[active=true]:text-fd-primary ' +
  "data-[active=true]:before:content-[''] data-[active=true]:before:bg-fd-primary " +
  'data-[active=true]:before:absolute data-[active=true]:before:w-px ' +
  'data-[active=true]:before:inset-y-2.5 data-[active=true]:before:inset-s-2.5';

function itemOffset(depth: number) {
  return `calc(${2 + 3 * depth} * var(--spacing))`;
}

// trailingSlash is on in next.config, so compare with the slash normalised off
const trimSlash = (s: string) => (s.length > 1 && s.endsWith('/') ? s.slice(0, -1) : s);

/**
 * Sidebar entry for one page. Splits the leading "12." off the title so the
 * numbers form an aligned column, marks the two milestone page kinds (part
 * review, boss challenge) with an icon instead, and shows a tick once the
 * chapter is complete.
 */
export function ChapterItem({ item }: { item: PageTree.Item }) {
  const pathname = usePathname();
  const depth = useFolderDepth();
  const progress = useProgress();

  const url = String(item.url);
  const name = String(item.name);
  const numbered = name.match(/^(\d+)\.\s*(.+)$/);
  const chapter = chapterIdFromUrl(url);
  const done = !!(chapter && progress?.done[chapter]);

  const isBoss = /\/boss\d*-/.test(url);
  const isReview = !numbered && !isBoss && /Review/i.test(name);
  const milestone = isBoss || isReview;

  return (
    <SidebarItem
      href={item.url}
      external={item.external}
      active={trimSlash(pathname) === trimSlash(url)}
      className={cn(ITEM_BASE, milestone && 'font-medium text-fd-foreground/80')}
      style={{ paddingInlineStart: itemOffset(depth) }}
    >
      {/* fixed-width gutter keeps every title on the same left edge */}
      <span className="mt-px w-5 shrink-0 text-end text-xs tabular-nums opacity-60">
        {numbered ? numbered[1] : null}
        {isBoss && <Trophy className="ms-auto size-3.5" />}
        {isReview && <ClipboardCheck className="ms-auto size-3.5" />}
      </span>
      <span className="min-w-0 flex-1 leading-snug">
        {numbered ? numbered[2] : name}
      </span>
      {done && (
        <Check
          aria-label="Chapter complete"
          className="mt-0.5 size-3.5 shrink-0 text-green-500"
        />
      )}
    </SidebarItem>
  );
}

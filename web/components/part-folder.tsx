'use client';
import {
  SidebarFolder,
  SidebarFolderContent,
  SidebarFolderTrigger,
  useFolderDepth,
} from 'fumadocs-ui/components/sidebar/base';
import type * as PageTree from 'fumadocs-core/page-tree';
import { useTreePath } from 'fumadocs-ui/contexts/tree';
import { cn } from '@/lib/cn';
import { chapterIdFromUrl, useProgress } from '@/lib/progress';

// Mirrors fumadocs' internal itemVariants (button variant) from
// layouts/docs/slots/sidebar, which is not exported. Re-check on upgrade.
const TRIGGER_BASE =
  'relative flex w-full flex-row items-center gap-2 rounded-lg p-2 text-start ' +
  'wrap-anywhere transition-colors hover:bg-fd-accent/50 ' +
  'hover:text-fd-accent-foreground/80 hover:transition-none ' +
  '[&_svg]:size-4 [&_svg]:shrink-0';

function triggerOffset(depth: number) {
  return `calc(${2 + 3 * (depth - 1)} * var(--spacing))`;
}

/** Chapter numbers ("09") of every numbered page directly inside this part. */
function chapterIds(item: PageTree.Folder): string[] {
  const ids: string[] = [];
  for (const child of item.children) {
    if (child.type !== 'page') continue;
    const id = chapterIdFromUrl(String(child.url));
    if (id) ids.push(id);
  }
  return ids;
}

/**
 * A part of the tutorial. Renders as a section header rather than another
 * link-looking row, so the parts read as headings and their chapters read as
 * the list underneath. Carries an x/y progress count on the right.
 */
export function PartFolder({
  item,
  children,
}: {
  item: PageTree.Folder;
  children: React.ReactNode;
}) {
  const depth = useFolderDepth() + 1;
  const progress = useProgress();
  // same signal fumadocs' own Folder uses: is this node on the active path?
  const active = useTreePath().includes(item);

  const ids = chapterIds(item);
  const done = progress ? ids.filter((id) => progress.done[id]).length : 0;
  const complete = ids.length > 0 && done === ids.length;

  return (
    <SidebarFolder active={active} className="mt-3 first:mt-0">
      <SidebarFolderTrigger
        className={cn(
          TRIGGER_BASE,
          'text-[0.7rem] font-semibold uppercase tracking-wider text-fd-foreground/70',
        )}
        style={{ paddingInlineStart: triggerOffset(depth) }}
      >
        <span className="min-w-0 flex-1">{item.name}</span>
        {ids.length > 0 && (
          <span
            className={cn(
              'shrink-0 text-[0.65rem] font-medium tabular-nums',
              complete ? 'text-green-500' : 'text-fd-muted-foreground',
            )}
          >
            {done}/{ids.length}
          </span>
        )}
      </SidebarFolderTrigger>
      <SidebarFolderContent>{children}</SidebarFolderContent>
    </SidebarFolder>
  );
}

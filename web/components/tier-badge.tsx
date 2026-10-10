import { cn } from '@/lib/cn';

export type Tier = 'foundations' | 'professional' | 'expert';

const LABEL: Record<Tier, string> = {
  foundations: 'Foundations',
  professional: 'Professional',
  expert: 'Expert',
};

// One tone per tier, the same three the homepage tier cards use.
const TONE: Record<Tier, string> = {
  foundations: 'bg-(--tone-sage)',
  professional: 'bg-(--tone-sky)',
  expert: 'bg-(--tone-violet)',
};

/** The small tier pill under a chapter title, so a reader knows where they are entering. */
export function TierBadge({ tier, track }: { tier: Tier; track?: string }) {
  return (
    <p className="not-prose mt-3 flex flex-wrap items-center gap-2 text-xs">
      {track ? (
        <span className="rounded-full border px-2.5 py-0.5 font-medium text-fd-muted-foreground">
          {track}
        </span>
      ) : null}
      <span
        className={cn(
          'rounded-full px-2.5 py-0.5 font-semibold uppercase tracking-wider text-fd-foreground/80',
          TONE[tier],
        )}
      >
        {LABEL[tier]}
      </span>
    </p>
  );
}

import Link from 'next/link';
import { cn } from '@/lib/cn';

const TONES = {
  plain: 'bg-fd-card',
  sage: 'bg-(--tone-sage)',
  sand: 'bg-(--tone-sand)',
  sky: 'bg-(--tone-sky)',
  violet: 'bg-(--tone-violet)',
} as const;

export type Tone = keyof typeof TONES;

/**
 * A surface. Big radius and a muted tint are what make a group of these read
 * as one system instead of as generic bordered boxes.
 */
export function Card({
  title,
  eyebrow,
  href,
  tone = 'plain',
  icon,
  className,
  children,
}: {
  title?: string;
  eyebrow?: string;
  href?: string;
  tone?: Tone;
  icon?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}) {
  const inner = (
    <>
      {(eyebrow || icon) && (
        <div className="not-prose mb-3 flex items-center gap-2 text-fd-muted-foreground">
          {icon}
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        </div>
      )}
      {title && (
        <h3 className="not-prose mb-2 text-base font-semibold tracking-tight text-fd-foreground">
          {title}
        </h3>
      )}
      {children && (
        <div
          className={cn(
            'prose-no-margin text-sm text-fd-muted-foreground',
            // links inside a card still need to look clickable
            '[&_a]:font-medium [&_a]:text-fd-primary [&_a]:underline [&_a]:underline-offset-2',
          )}
        >
          {children}
        </div>
      )}
    </>
  );

  const shared = cn(
    'block rounded-(--radius-card) border border-fd-border/60 p-5 md:p-6',
    TONES[tone],
    href &&
      'transition-all duration-300 ease-(--ease-out-soft) hover:-translate-y-0.5 hover:border-fd-primary/40 hover:shadow-(--shadow-card)',
    className,
  );

  if (href) {
    return (
      <Link href={href} className={cn(shared, 'no-underline')}>
        {inner}
      </Link>
    );
  }
  return <div className={shared}>{inner}</div>;
}

/** Responsive grid of cards. Defaults to two up, pass cols for three. */
export function CardGrid({
  cols = 2,
  className,
  children,
}: {
  cols?: 2 | 3;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        'not-prose my-6 grid gap-4',
        cols === 3 ? 'sm:grid-cols-2 lg:grid-cols-3' : 'sm:grid-cols-2',
        className,
      )}
    >
      {children}
    </div>
  );
}

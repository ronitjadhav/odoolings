import { cn } from '@/lib/cn';

const LETTERS: readonly {
  character: string;
  family: string;
  signal?: boolean;
}[] = [
  { character: 'O', family: 'var(--font-geist-pixel-square)' },
  { character: 'D', family: 'var(--font-geist-pixel-grid)' },
  { character: 'O', family: 'var(--font-geist-pixel-circle)' },
  { character: 'O', family: 'var(--font-geist-pixel-triangle)' },
  { character: 'L', family: 'var(--font-geist-pixel-line)', signal: true },
  { character: 'I', family: 'var(--font-geist-pixel-square)', signal: true },
  { character: 'N', family: 'var(--font-geist-pixel-grid)', signal: true },
  { character: 'G', family: 'var(--font-geist-pixel-circle)', signal: true },
  { character: 'S', family: 'var(--font-geist-pixel-line)', signal: true },
] as const;

function PixelLetters({ interactive = false }: { interactive?: boolean }) {
  return LETTERS.map(({ character, family, signal }, index) => (
    <span
      aria-hidden="true"
      className={cn(
        'inline-block',
        interactive &&
          'transition-transform duration-500 ease-(--ease-out-soft) hover:-translate-y-[0.04em] motion-reduce:transition-none motion-reduce:hover:translate-y-0',
        signal && 'text-fd-primary',
      )}
      key={`${character}-${index}`}
      style={{ fontFamily: family }}
    >
      {character}
    </span>
  ));
}

/** Compact brand mark for the home and docs navigation bars. */
export function OdoolingsLogo() {
  return (
    <span className="inline-flex rounded-full bg-(--tone-violet) px-4 py-2.5 transition-transform duration-300 ease-(--ease-out-soft) hover:scale-[1.03] motion-reduce:transition-none motion-reduce:hover:scale-100">
      <span className="sr-only">Odoolings</span>
      <span
        aria-hidden="true"
        className="inline-flex items-baseline whitespace-nowrap text-[1.35rem] leading-none font-normal tracking-[-0.075em] uppercase"
      >
        <PixelLetters />
      </span>
    </span>
  );
}

/**
 * The display wordmark mixes Geist's pixel alphabets letter by letter. The
 * treatment echoes the checker-at-work idea without making body copy harder
 * to read, and keeps the Odoo/violet split unique to this project.
 */
export function OdoolingsWordmark({ className }: { className?: string }) {
  return (
    <h1
      aria-label="Odoolings"
      className={cn(
        'm-0 flex w-full items-baseline justify-center whitespace-nowrap text-[clamp(3.25rem,13.5vw,11rem)] leading-[0.72] font-normal tracking-[-0.09em] uppercase',
        className,
      )}
    >
      <PixelLetters interactive />
    </h1>
  );
}

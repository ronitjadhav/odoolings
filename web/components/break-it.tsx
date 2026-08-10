import { Icon } from './icon';

/** A small marker for break-it labs, so a deliberate traceback reads as deliberate. */
export function BreakIt() {
  return (
    <p className="not-prose mb-3 inline-flex items-center gap-1.5 rounded-full bg-(--tone-sand) px-3 py-1 text-xs font-semibold uppercase tracking-wider text-fd-primary">
      <Icon name="warn" /> Break-it lab
    </p>
  );
}

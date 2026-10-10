import { ChevronDown } from 'lucide-react';
import type { ReactNode } from 'react';
import { CopyOnlyCodeBlock } from './copy-button';
import { Icon } from './icon';

// Chapters with nothing to rebuild: reading only, setup itself, or work outside Odoo.
const NO_SETUP = new Set(['01', '02', '03', '04', '05', '07', '43', '45', '47', '48', '55']);
// Chapters that create their database themselves: the reader only needs chapter 5.
const BUILDS_ITS_OWN = new Set(['21']);

const FETCH = 'curl -O https://raw.githubusercontent.com/ronitjadhav/odoolings/main/code/odoolings.py';
const SETUP = '/docs/01-environment/05-dev-setup-with-docker-compose';

/** A console block in the site's style: `$` prompts shown, only the commands copied. */
function Console({ commands }: { commands: string[] }) {
  return (
    <CopyOnlyCodeBlock copyText={commands.join('\n')} className="my-0">
      <code>
        {commands.map((command, i) => (
          <span key={command} className="line">
            <span className="select-none text-fd-muted-foreground">$ </span>
            {command}
            {i < commands.length - 1 ? '\n' : null}
          </span>
        ))}
      </code>
    </CopyOnlyCodeBlock>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: ReactNode }) {
  return (
    <li className="flex gap-3">
      <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-fd-primary text-xs font-semibold text-fd-primary-foreground">
        {n}
      </span>
      <div className="min-w-0 flex-1 space-y-2">
        <p className="font-medium text-fd-foreground">{title}</p>
        {children}
      </div>
    </li>
  );
}

/** "Starting at chapter N?": how to get a chapter's starting state without the earlier ones. */
export function JumpIn({ chapter }: { chapter: string }) {
  if (NO_SETUP.has(chapter)) return null;
  const isNumber = /^\d+$/.test(chapter);
  const name = isNumber ? `ch${chapter}` : chapter;
  const ownDb = BUILDS_ITS_OWN.has(chapter);

  return (
    <details className="group my-6 rounded-2xl border bg-fd-card text-sm transition-colors hover:border-fd-primary/30 open:border-fd-primary/30">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3 [&::-webkit-details-marker]:hidden">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-fd-primary/10 text-fd-primary">
          <Icon name="rocket" size={18} weight="fill" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-semibold text-fd-foreground">
            {isNumber ? `Starting at chapter ${Number(chapter)}?` : 'Starting with this boss level?'}
          </span>
          <span className="block text-xs text-fd-muted-foreground">
            {ownDb
              ? 'Only the environment from chapter 5 is needed.'
              : 'One command sets up everything the earlier chapters built.'}
          </span>
        </span>
        <ChevronDown className="size-4 shrink-0 text-fd-muted-foreground transition-transform duration-200 group-open:rotate-180" />
      </summary>

      <div className="border-t px-4 py-4">
        <ol className="space-y-4">
          <Step n={1} title="Have the environment running">
            <p className="text-fd-muted-foreground">
              Your copy of the starter with{' '}
              <code className="whitespace-nowrap rounded bg-fd-muted px-1 py-0.5 font-mono text-[0.85em] text-fd-foreground">
                docker compose up -d
              </code>
              , as set up in{' '}
              <a href={SETUP} className="font-medium text-fd-primary underline underline-offset-2">
                chapter 5
              </a>
              .
            </p>
          </Step>
          <Step n={2} title={ownDb ? 'In that folder, get the checker' : 'In that folder, run'}>
            <Console commands={ownDb ? [FETCH] : [FETCH, `python3 odoolings.py start ${name}`]} />
          </Step>
        </ol>
        <p className="mt-4 flex items-start gap-2 text-xs text-fd-muted-foreground">
          <Icon name="ok" size={14} className="mt-px shrink-0 text-fd-primary" />
          {ownDb
            ? 'This chapter builds its own database from its first step.'
            : 'It shows its plan before changing anything and keeps backups, so it is also your way back to a clean start.'}
        </p>
      </div>
    </details>
  );
}

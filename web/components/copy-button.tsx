'use client';

import type { ComponentProps } from 'react';
import { Check, Clipboard } from 'lucide-react';
import { CodeBlock, Pre } from 'fumadocs-ui/components/codeblock';
import { useCopyButton } from 'fumadocs-ui/utils/use-copy-button';
import { cn } from '@/lib/cn';

/**
 * Wraps fumadocs' CodeBlock with a copy button that copies `copyText` (the block's typed
 * input, prompts stripped and output lines dropped, see lib/copy-only-input.ts) instead of
 * the rendered DOM. This has to live in a client component: CodeBlock is client-only, and
 * the `Actions` render prop it needs is a function, which can't cross the server/client
 * boundary from the server-rendered MDX `pre` mapping in components/mdx.tsx.
 */
export function CopyOnlyCodeBlock({
  copyText,
  children,
  ...rest
}: ComponentProps<typeof CodeBlock> & { copyText: string }) {
  return (
    <CodeBlock
      {...rest}
      allowCopy={false}
      Actions={({ className }) => (
        <div className={className}>
          <CopyOnlyButton text={copyText} />
        </div>
      )}
    >
      <Pre>{children}</Pre>
    </CodeBlock>
  );
}

function CopyOnlyButton({ text, className }: { text: string; className?: string }) {
  const [checked, onClick] = useCopyButton(() => navigator.clipboard.writeText(text));

  return (
    <button
      type="button"
      data-checked={checked || undefined}
      onClick={onClick}
      aria-label={checked ? 'Copied' : 'Copy code'}
      className={cn(
        'inline-flex items-center justify-center rounded-md p-1 text-fd-muted-foreground transition-colors duration-100 hover:bg-fd-accent hover:text-fd-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fd-ring [&_svg]:size-4',
        className,
      )}
    >
      {checked ? <Check /> : <Clipboard />}
    </button>
  );
}

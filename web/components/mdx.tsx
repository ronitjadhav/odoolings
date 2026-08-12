import defaultMdxComponents from 'fumadocs-ui/mdx';
import type { MDXComponents } from 'mdx/types';
import { Steps, Step } from 'fumadocs-ui/components/steps';
import { Files, File, Folder } from 'fumadocs-ui/components/files';
import { Quiz } from '@/components/quiz';
import { Mermaid } from '@/components/mermaid';
import { Term } from '@/components/term';
import { Mastery } from '@/components/mastery';
import { Card, CardGrid } from '@/components/card';
import { Icon } from '@/components/icon';
import { BreakIt } from '@/components/break-it';
import { MigrationChecklist } from '@/components/migration-checklist';
import { CopyOnlyCodeBlock } from '@/components/copy-button';

// ```console/```python blocks stash their prompt-stripped, output-dropped copy text as
// `data-copy` (see lib/copy-only-input.ts). When present, swap in a copy button that uses
// that string verbatim instead of fumadocs' default, which copies the rendered DOM as-is.
// Every other code fence (xml, csv, text...) falls through to fumadocs' own `pre` unchanged.
function pre(props: Parameters<NonNullable<typeof defaultMdxComponents.pre>>[0] & { 'data-copy'?: string }) {
  const { 'data-copy': copyText, children, ...rest } = props;
  if (copyText === undefined) return defaultMdxComponents.pre!(props);

  return (
    <CopyOnlyCodeBlock {...rest} copyText={copyText}>
      {children}
    </CopyOnlyCodeBlock>
  );
}

export function getMDXComponents(components?: MDXComponents) {
  return {
    ...defaultMdxComponents,
    pre,
    Quiz,
    Mermaid,
    Term,
    Mastery,
    Card,
    CardGrid,
    Icon,
    Steps,
    Step,
    Files,
    File,
    Folder,
    BreakIt,
    MigrationChecklist,
    ...components,
  } satisfies MDXComponents;
}

export const useMDXComponents = getMDXComponents;

declare global {
  type MDXProvidedComponents = ReturnType<typeof getMDXComponents>;
}

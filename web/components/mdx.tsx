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

export function getMDXComponents(components?: MDXComponents) {
  return {
    ...defaultMdxComponents,
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
    ...components,
  } satisfies MDXComponents;
}

export const useMDXComponents = getMDXComponents;

declare global {
  type MDXProvidedComponents = ReturnType<typeof getMDXComponents>;
}

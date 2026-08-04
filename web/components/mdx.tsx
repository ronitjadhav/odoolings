import defaultMdxComponents from 'fumadocs-ui/mdx';
import type { MDXComponents } from 'mdx/types';
import { Quiz } from '@/components/quiz';
import { Mermaid } from '@/components/mermaid';
import { Term } from '@/components/term';
import { Mastery } from '@/components/mastery';
import { Card, CardGrid } from '@/components/card';

export function getMDXComponents(components?: MDXComponents) {
  return {
    ...defaultMdxComponents,
    Quiz,
    Mermaid,
    Term,
    Mastery,
    Card,
    CardGrid,
    ...components,
  } satisfies MDXComponents;
}

export const useMDXComponents = getMDXComponents;

declare global {
  type MDXProvidedComponents = ReturnType<typeof getMDXComponents>;
}

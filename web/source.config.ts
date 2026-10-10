import { defineConfig, defineDocs } from 'fumadocs-mdx/config';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';
import { z } from 'zod';
import { rehypeCodeDefaultOptions } from 'fumadocs-core/mdx-plugins';
import { transformerCopyOnlyInput } from './lib/copy-only-input';

// You can customize Zod schemas for frontmatter and `meta.json` here
// see https://fumadocs.dev/docs/mdx/collections
export const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    // deep-dive chapters declare their tier; journey chapters get it from their Part
    schema: pageSchema.extend({
      tier: z.enum(['foundations', 'professional', 'expert']).optional(),
    }),
    postprocess: {
      includeProcessedMarkdown: true,
    },
  },
  meta: {
    schema: metaSchema,
  },
});

export default defineConfig({
  mdxOptions: {
    rehypeCodeOptions: {
      ...rehypeCodeDefaultOptions,
      transformers: [...(rehypeCodeDefaultOptions.transformers ?? []), transformerCopyOnlyInput()],
    },
  },
});

import type { MetadataRoute } from 'next';
import { source } from '@/lib/source';
import { isIndexableDocsPage } from '@/lib/seo';
import { canonicalUrl } from '@/lib/shared';
export const dynamic = 'force-static';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: canonicalUrl(),
      changeFrequency: 'weekly',
      priority: 1,
    },
    ...source
      .getPages()
      .filter(isIndexableDocsPage)
      .map((page) => ({
        url: canonicalUrl(page.url),
        changeFrequency: 'monthly' as const,
        priority: page.url === '/docs' ? 0.9 : 0.7,
      })),
  ];
}

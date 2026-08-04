import type { MetadataRoute } from 'next';
import { source } from '@/lib/source';
export const dynamic = 'force-static';

import { siteUrl } from '@/lib/shared';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${siteUrl}/`,
      changeFrequency: 'weekly',
      priority: 1,
    },
    ...source.getPages().map((page) => ({
      url: `${siteUrl}${page.url}`,
      changeFrequency: 'monthly' as const,
      priority: page.url === '/docs' ? 0.9 : 0.7,
    })),
  ];
}

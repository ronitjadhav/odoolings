import type { MetadataRoute } from 'next';
import { basePath, siteUrl } from '@/lib/shared';
export const dynamic = 'force-static';


export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: `${basePath}/`,
    },
    host: siteUrl,
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}

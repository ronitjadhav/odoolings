import type { MetadataRoute } from 'next';
import { appDescription, appName, basePath } from '@/lib/shared';
export const dynamic = 'force-static';


export default function manifest(): MetadataRoute.Manifest {
  return {
    name: appName,
    short_name: appName,
    description: appDescription,
    start_url: `${basePath}/`,
    scope: `${basePath}/`,
    display: 'standalone',
    background_color: '#f7f6f1',
    theme_color: '#7654d6',
    icons: [
      {
        src: `${basePath}/brand/odoolings-avatar-paper.png`,
        sizes: '1024x1024',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: `${basePath}/brand/odoolings-avatar-ink.png`,
        sizes: '1024x1024',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}

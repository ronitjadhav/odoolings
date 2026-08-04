import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { OdoolingsLogo } from '@/components/odoolings-wordmark';
import { gitConfig } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: <OdoolingsLogo />,
    },
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}

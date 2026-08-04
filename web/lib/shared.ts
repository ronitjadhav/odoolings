export const appName = 'Odoolings';
export const appDescription =
  'A hands-on Odoo 19 development tutorial: build one real app from your first module to OCA-quality contributions.';
// Must match next.config.mjs's basePath (that file can't import this one: it
// loads before TypeScript transpilation is available). Empty because the site
// is served from the root of a custom domain (see public/CNAME), not a GitHub
// Pages project-page subpath.
export const basePath = '';
export const siteOrigin = 'https://odoolings.ronit.io';
export const siteUrl = `${siteOrigin}${basePath}`;
export const socialCard = `${basePath}/brand/odoolings-social-card-ink.png`;
export const docsRoute = '/docs';
export const docsImageRoute = '/og/docs';
export const docsContentRoute = '/llms.mdx/docs';

export const gitConfig = {
  user: 'ronitjadhav',
  repo: 'odoolings',
  branch: 'main',
};

export const TOTAL_CHAPTERS = 40;

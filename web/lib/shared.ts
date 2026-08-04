export const appName = 'Odoolings';
export const homeTitle = 'Odoolings: Free Odoo 19 Development Tutorial';
export const appDescription =
  'Learn Odoo 19 development for free by building a real module. Hands-on lessons cover Python, ORM, views, security, testing, OWL, and OCA practices.';
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

/** Canonical page URLs always match Next's trailingSlash export setting. */
export function canonicalUrl(path = '/') {
  const route = path.startsWith('/') ? path : `/${path}`;
  const normalizedRoute = route === '/' ? route : `${route.replace(/\/$/, '')}/`;

  return `${siteUrl}${normalizedRoute}`;
}

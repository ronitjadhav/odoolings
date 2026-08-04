import { canonicalUrl } from './shared';

export const unpublishedPageDescription = 'Not written yet, tracked in the roadmap.';
export const courseName = 'Free Odoo 19 Development Tutorial';
export const courseId = `${canonicalUrl()}#course`;
export const authorId = `${canonicalUrl()}#author`;

/** Stub lessons stay navigable, but should not compete with complete lessons in search. */
export function isIndexableDocsPage(page: { data: { description?: string } }) {
  return page.data.description !== unpublishedPageDescription;
}

import { getPageImage, getPageMarkdownUrl, source } from '@/lib/source';
import {
  DocsBody,
  DocsDescription,
  DocsPage,
  DocsTitle,
  MarkdownCopyButton,
  ViewOptionsPopover,
} from 'fumadocs-ui/layouts/docs/page';
import { notFound } from 'next/navigation';
import { JsonLd } from '@/components/json-ld';
import { getMDXComponents } from '@/components/mdx';
import type { Metadata } from 'next';
import { createRelativeLink } from 'fumadocs-ui/mdx';
import { chapterIdFromUrl } from '@/lib/chapter-id';
import { authorId, courseId, courseName, isIndexableDocsPage } from '@/lib/seo';
import { appName, basePath, canonicalUrl, gitConfig } from '@/lib/shared';
import { MarkComplete } from '@/components/mark-complete';

export default async function Page(props: PageProps<'/docs/[[...slug]]'>) {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  const MDX = page.data.body;
  const markdownUrl = getPageMarkdownUrl(page).url;
  const pageUrl = canonicalUrl(page.url);
  const published = isIndexableDocsPage(page);

  const breadcrumbItems: Record<string, unknown>[] = [
    {
      '@type': 'ListItem',
      position: 1,
      name: appName,
      item: canonicalUrl(),
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Tutorial',
      item: canonicalUrl('/docs'),
    },
  ];

  if (page.url !== '/docs') {
    breadcrumbItems.push({
      '@type': 'ListItem',
      position: 3,
      name: page.data.title,
      item: pageUrl,
    });
  }

  const structuredGraph: Record<string, unknown>[] = [
    {
      '@type': 'BreadcrumbList',
      '@id': `${pageUrl}#breadcrumb`,
      itemListElement: breadcrumbItems,
    },
  ];

  const chapterId = chapterIdFromUrl(page.url);
  if (chapterId !== null) {
    structuredGraph.push({
      '@type': 'LearningResource',
      '@id': `${pageUrl}#lesson`,
      url: pageUrl,
      name: page.data.title,
      description: page.data.description,
      position: Number(chapterId),
      inLanguage: 'en',
      isAccessibleForFree: true,
      learningResourceType: 'Lesson',
      teaches: page.data.title.replace(/^\d+\.\s*/, ''),
      isPartOf: {
        '@type': 'Course',
        '@id': courseId,
        url: canonicalUrl(),
        name: courseName,
      },
      author: {
        '@type': 'Person',
        '@id': authorId,
        name: 'Ronit Jadhav',
        url: 'https://github.com/ronitjadhav',
      },
    });
  }

  const structuredData = published
    ? {
        '@context': 'https://schema.org',
        '@graph': structuredGraph,
      }
    : null;

  return (
    <>
      {structuredData ? <JsonLd data={structuredData} /> : null}
      <DocsPage toc={page.data.toc} full={page.data.full}>
        <DocsTitle>{page.data.title}</DocsTitle>
        <DocsDescription className="mb-0">{page.data.description}</DocsDescription>
        <div className="flex flex-row gap-2 items-center border-b pb-6">
          <MarkdownCopyButton markdownUrl={markdownUrl} />
          <ViewOptionsPopover
            markdownUrl={markdownUrl}
            githubUrl={`https://github.com/${gitConfig.user}/${gitConfig.repo}/blob/${gitConfig.branch}/web/content/docs/${page.path}`}
          />
        </div>
        <DocsBody>
          <MDX
            components={getMDXComponents({
              // this allows you to link to other pages with relative file paths
              a: createRelativeLink(source, page),
            })}
          />
        </DocsBody>
        <MarkComplete />
      </DocsPage>
    </>
  );
}

export async function generateStaticParams() {
  return source.generateParams();
}

export async function generateMetadata(props: PageProps<'/docs/[[...slug]]'>): Promise<Metadata> {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  const pageUrl = canonicalUrl(page.url);
  const published = isIndexableDocsPage(page);
  const imageUrl = `${basePath}${getPageImage(page).url}`;

  return {
    title: page.data.title,
    description: page.data.description,
    robots: published ? undefined : { index: false, follow: true },
    alternates: {
      canonical: pageUrl,
    },
    openGraph: {
      type: 'article',
      url: pageUrl,
      siteName: appName,
      title: page.data.title,
      description: page.data.description,
      images: [imageUrl],
    },
    twitter: {
      card: 'summary_large_image',
      title: page.data.title,
      description: page.data.description,
      images: [imageUrl],
    },
  };
}

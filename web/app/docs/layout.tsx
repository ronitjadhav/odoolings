import { source } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { baseOptions } from '@/lib/layout.shared';
import { ChapterItem } from '@/components/chapter-item';
import { PartFolder } from '@/components/part-folder';

export default function Layout({ children }: LayoutProps<'/docs'>) {
  return (
    <DocsLayout
      tree={source.getPageTree()}
      {...baseOptions()}
      sidebar={{ components: { Item: ChapterItem, Folder: PartFolder } }}
    >
      {children}
    </DocsLayout>
  );
}
